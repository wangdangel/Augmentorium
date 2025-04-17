"""
Indexer for Augmentorium
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from queue import Queue
import pathspec # Ensure pathspec is imported

from config.manager import ConfigManager
# Import constants needed from defaults
from config.defaults import PROJECT_INTERNAL_DIR_NAME, DEFAULT_LOG_DIR # Ensure DEFAULT_LOG_DIR is imported
from utils.db_utils import VectorDB
from utils.logging import ProjectLogger
from utils.path_utils import get_path_hash_key # Import the missing function
from indexer.watcher_service import FileWatcherService
from indexer.file_event import FileEvent
from indexer.file_hasher import FileHasher
from indexer.chunker import Chunker
from indexer.code_chunk import CodeChunk
from indexer.embedder import OllamaEmbedder, ChunkEmbedder, ChunkProcessor

logger = logging.getLogger(__name__)

class Indexer:
    """Main indexer for Augmentorium"""

    def close(self):
        """Close all resources"""
        import gc
        try:
            if hasattr(self, "logger"):
                self.logger.info("[CLOSE] Starting resource cleanup in indexer.")
            # Close vector DB if it has a close method
            if hasattr(self, "vector_db") and self.vector_db is not None:
                if hasattr(self.vector_db, "close"):
                    self.logger.info("[CLOSE] Calling vector_db.close()")
                    self.vector_db.close()
                # Explicitly dereference ChromaDB client if present
                if hasattr(self.vector_db, "client"):
                    self.logger.info("[CLOSE] Deleting vector_db.client reference")
                    del self.vector_db.client
                    self.vector_db.client = None
                self.logger.info("[CLOSE] Deleting vector_db reference")
                del self.vector_db
                self.vector_db = None
            # Force garbage collection
            self.logger.info("[CLOSE] Forcing garbage collection")
            gc.collect()
            self.logger.info("[CLOSE] Resource cleanup complete")
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"[CLOSE] Exception during resource cleanup: {e}")
            else:
                logger.error(f"[CLOSE] Exception during resource cleanup: {e}")
        # TODO: Close graph DB connections if persistent (currently opened per operation)
        # TODO: Stop any file watchers if running
        # Placeholder for future cleanup logic

    def pause(self):
        """Pause the indexer by closing all resources (safe for .Augmentorium deletion)"""
        self.close()

    def resume(self):
        """Resume the indexer by re-initializing the vector DB handle"""
        try:
            db_path = self.config_manager.get_db_path(self.project_path)
            self.vector_db = VectorDB(db_path)
        except Exception as e:
            self.logger.error(f"Failed to resume vector DB: {e}")

    def __init__(
        self,
        config_manager: ConfigManager,
        project_path: str
        # Remove file_watcher_service reference
    ):
        # Status tracking
        self.status = "idle"
        self.last_indexed = None
        self.error = None
        """
        Initialize indexer
        
        Args:
            config_manager: Configuration manager
            project_path: Path to the project
            # Remove file_watcher_service from Args
        """
        self.config_manager = config_manager
        self.project_path = os.path.abspath(project_path)
        self.config = config_manager.config # Get reference to the single root config

        # Find project name from the central registry
        self.project_name = "unknown_project" # Default
        for name, path in config_manager.get_all_projects().items():
            if path == self.project_path:
                self.project_name = name
                break
        if self.project_name == "unknown_project":
             # This shouldn't happen if indexer is created correctly via service
             logger.error(f"Could not find project name for path {self.project_path} in config registry.")
             # Consider raising an error or handling appropriately

        # Set up project logger
        self.logger = ProjectLogger(self.project_name)

        # Set up vector database using path from ConfigManager
        db_path = config_manager.get_db_path(self.project_path)
        self.vector_db = VectorDB(db_path)

        # Initialize graph database if needed using path from ConfigManager
        try:
            graph_db_path = config_manager.get_graph_db_path(self.project_path)
            if not os.path.exists(graph_db_path):
                # Graph DB initialization logic remains the same, just uses the correct path
                from utils.graph_db import get_connection
                conn = get_connection(graph_db_path)
                c = conn.cursor()
                c.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    name TEXT,
                    file_path TEXT,
                    start_line INTEGER,
                    end_line INTEGER,
                    metadata TEXT
                )
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT,
                    target_id TEXT,
                    relation_type TEXT,
                    metadata TEXT
                )
                """)
                c.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)")
                conn.commit()
                conn.close()
                self.logger.info(f"Graph database initialized at {graph_db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize graph database: {e}")

        # Set up Ollama embedder - Read directly from the single config
        ollama_config = self.config.get("ollama", {})
        ollama_base_url = ollama_config.get("base_url", "http://localhost:11434")
        ollama_model = ollama_config.get("embedding_model", "bge-m3:latest")
        ollama_batch_size = ollama_config.get("embedding_batch_size", 10)

        self.ollama_embedder = OllamaEmbedder(
            base_url=ollama_base_url,
            model=ollama_model,
            batch_size=ollama_batch_size
        )
        self.logger.info(f"Initialized OllamaEmbedder with model: {ollama_model}, base_url: {ollama_base_url}, batch_size: {ollama_batch_size}")

        # Set up chunker - Read directly from the single config
        chunking_config = self.config.get("chunking", {})
        self.chunker = Chunker(chunking_config)

        # Set up chunk processor - Read directly from the single config
        indexer_config = self.config.get("indexer", {})
        chunk_embedder_batch_size = ollama_batch_size # Use the same batch size for consistency
        chunk_embedder_max_workers = indexer_config.get("max_workers", 4)

        self.chunk_processor = ChunkProcessor(
            vector_db=self.vector_db,
            embedder=ChunkEmbedder(
                ollama_embedder=self.ollama_embedder,
                batch_size=chunk_embedder_batch_size,
                max_workers=chunk_embedder_max_workers
            )
        )

        # Load ignore patterns: base from config + project-specific from .augmentoriumignore
        base_ignore_patterns = indexer_config.get("ignore_patterns", [])
        project_ignore_patterns = []
        project_ignore_file = config_manager.get_project_ignore_file_path(self.project_path)

        if os.path.exists(project_ignore_file):
            try:
                with open(project_ignore_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'): # Ignore comments and blank lines
                            project_ignore_patterns.append(line)
                self.logger.info(f"Loaded {len(project_ignore_patterns)} patterns from {project_ignore_file}")
            except Exception as e:
                self.logger.warning(f"Failed to read project ignore file {project_ignore_file}: {e}")

        # Combine and deduplicate patterns
        combined_patterns = list(set(base_ignore_patterns + project_ignore_patterns))
        # Ensure .Augmentorium is always ignored
        augmentorium_patterns = ["**/.Augmentorium/**"]
        for pattern in augmentorium_patterns:
            if pattern not in combined_patterns:
                combined_patterns.append(pattern)
        self.logger.info(f"Final ignore patterns: {combined_patterns}")
        self.ignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", combined_patterns)
        self.logger.info(f"Initialized with {len(combined_patterns)} combined ignore patterns (including .Augmentorium).")

        # Initialize file hasher and load cache from project's metadata directory
        metadata_dir = self.config_manager.get_metadata_path(self.project_path)
        self.hash_cache_file = os.path.join(metadata_dir, "hash_cache.json")
        self.file_hasher = FileHasher()
        try:
            self.file_hasher.load_cache(self.hash_cache_file)
        except Exception as e:
            self.logger.warning(f"Failed to load hash cache from {self.hash_cache_file}: {e}")
        
        self.logger.info(f"Initialized indexer for project: {self.project_name}")
    
    def close(self):
        """Close all resources"""
        try:
            # Save hash cache before closing
            try:
                self.file_hasher.save_cache(self.hash_cache_file)
            except Exception as e:
                self.logger.warning(f"Failed to save hash cache: {e}")
            # Close vector DB if it has a close method
            if hasattr(self.vector_db, "close"):
                self.vector_db.close()
        except Exception:
            pass
        # TODO: Close graph DB connections if persistent (currently opened per operation)
        # TODO: Stop any file watchers if running
        # Placeholder for future cleanup logic

    def process_file(self, file_path: str) -> int:
        """
        Process a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            int: Number of chunks processed
        """
        try:
            # Skip ignored files
            from utils.path_utils import get_relative_path
            rel_path = get_relative_path(file_path, self.project_path)
            if self.ignore_spec.match_file(rel_path):
                self.logger.info(f"Skipping ignored file: {file_path}")
                return 0
            
            self.logger.info(f"Processing file: {file_path}")
            
            self.logger.debug(f"Chunking file: {file_path}")
            chunks = self.chunker.chunk_file(file_path)
            self.logger.debug(f"Chunking complete: {file_path}, {len(chunks)} chunks")
            
            if not chunks:
                self.logger.warning(f"No chunks generated for file: {file_path}")
                return 0
            
            self.logger.info(f"Generated {len(chunks)} chunks for file: {file_path}")
            
            self.logger.debug(f"Embedding {len(chunks)} chunks for file: {file_path}")
            num_processed = self.chunk_processor.process_chunks(chunks, show_progress=False)
            self.logger.debug(f"Embedding complete: {file_path}")
            
            self.logger.info(f"Processed {num_processed} chunks for file: {file_path}")
            
            # --- Insert/update graph DB ---
            try:
                import json
                from utils.graph_db import get_connection, insert_or_update_node, insert_edge

                # Get graph DB path using ConfigManager method
                graph_db_path = self.config_manager.get_graph_db_path(self.project_path)
                conn = get_connection(graph_db_path)

                for chunk in chunks:
                    node_data = {
                        "id": chunk.id,
                        "type": chunk.chunk_type,
                        "name": chunk.name,
                        "file_path": chunk.file_path,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "metadata": chunk.metadata
                    }
                    insert_or_update_node(conn, node_data)

                    # Insert edges for references if present
                    refs = chunk.metadata.get("references", [])
                    for ref in refs:
                        # ref should be a dict: {"target": ..., "type": ...}
                        if isinstance(ref, dict):
                            target = ref.get("target")
                            rel_type = ref.get("type", "references")
                            if target:
                                insert_edge(conn, chunk.id, target, rel_type)
                        else:
                            # fallback: treat as old string style
                            insert_edge(conn, chunk.id, ref, "references")

                conn.commit()
                conn.close()
            except Exception as e:
                self.logger.warning(f"Failed to update graph DB for {file_path}: {e}")

            return num_processed
        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {e}")
            return 0
    
    def remove_file(self, file_path: str) -> bool:
        """
        Remove a file from the index
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Removing file from index: {file_path}")
            
            # Remove chunks for the file
            success = self.chunk_processor.remove_chunks(file_path)
            
            if success:
                self.logger.info(f"Successfully removed file from index: {file_path}")
            else:
                self.logger.error(f"Failed to remove file from index: {file_path}")
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to remove file {file_path}: {e}")
            return False
    
    def handle_file_event(self, event: FileEvent) -> None:
        """
        Handle a file event
        
        Args:
            event: File event
        """
        try:
            if event.is_directory:
                return
            
            self.logger.debug(f"Handling file event: {event}")
            
            if event.event_type in ["created", "modified"]:
                self.process_file(event.file_path)
            elif event.event_type == "deleted":
                self.remove_file(event.file_path)
        except Exception as e:
            self.logger.error(f"Failed to handle file event {event}: {e}")
    
    def full_index(self) -> int:
        """
        Perform a full index of the project
        
        Returns:
            int: Number of files processed
        """
        try:
            self.status = "indexing"
            self.error = None
            self.logger.info(f"Starting full index for project: {self.project_name}")

            # Call the static scan_project method directly from FileWatcherService
            # Pass the indexer's own ignore_spec
            events = FileWatcherService.scan_project(self.project_path, self.ignore_spec)

            # The scan_project method now handles filtering based on ignore_spec.

            self.logger.info(f"Found {len(events)} files to index after applying ignore patterns")

            # Process each file
            processed_count = 0
            skipped_count = 0
            # Iterate directly over events returned by scan_project
            for i, event in enumerate(events):
                # Check hash cache
                file_hash = self.file_hasher.compute_hash(event.file_path)
                # Use normalized path for hash key consistency
                key = get_path_hash_key(event.file_path) # Use helper function
                cached_hash = self.file_hasher.hash_cache.get(key)
                if cached_hash == file_hash:
                    self.logger.info(f"Skipping unchanged file: {event.relative_path}")
                    skipped_count += 1
                    continue
                # Update hash cache
                if file_hash:
                    self.file_hasher.hash_cache[key] = file_hash
                self.logger.info(f"Indexing file {i+1}/{len(events)}: {event.relative_path}")
                self.handle_file_event(event)
                processed_count += 1
            
            # Save updated hash cache
            try:
                self.file_hasher.save_cache(self.hash_cache_file)
            except Exception as e:
                self.logger.warning(f"Failed to save hash cache: {e}")
            
            self.logger.info(f"Full index completed for project: {self.project_name}")
            self.logger.info(f"Processed {processed_count} files, skipped {skipped_count} unchanged files")
            self.status = "idle"
            import datetime as _datetime
            self.last_indexed = _datetime.datetime.utcnow().isoformat() + "Z"
            return processed_count
        except Exception as e:
            self.logger.error(f"Failed to perform full index: {e}")
            self.status = "error"
            self.error = str(e)
            return 0


class IndexerService:
    """Service for indexing multiple projects"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize indexer service
        
        Args:
            config_manager: Configuration manager
        """
        self.config_manager = config_manager
        self.config = config_manager.config # Get reference to the single root config

        # Initialize projects
        self.indexers: Dict[str, Indexer] = {}

        # Initialize file watcher - Use settings from the single config
        indexer_config = self.config.get("indexer", {})
        general_config = self.config.get("general", {})
        log_dir = general_config.get("log_dir", DEFAULT_LOG_DIR) # Use fallback default if needed
        # Use the same specific subdir for file watcher cache
        cache_dir = os.path.join(log_dir, "indexer_cache")
        os.makedirs(cache_dir, exist_ok=True) # Ensure it exists

        self.file_watcher = FileWatcherService(
            config_manager,
            polling_interval=indexer_config.get("polling_interval", 1.0),
            hash_algorithm=indexer_config.get("hash_algorithm", "md5"),
            cache_dir=cache_dir,
            event_callback=self._handle_file_event
        )
        
        self.running = False
        self.check_thread = None
        
        logger.info("Initialized indexer service")

    def pause(self):
        """Pause all managed indexers (release DB/file handles)"""
        for idx in self.indexers.values():
            idx.pause()

    def resume(self):
        """Resume all managed indexers (re-establish DB/file handles)"""
        for idx in self.indexers.values():
            idx.resume()
    
    def add_project(self, project_path: str) -> bool:
        """
        Add a project to index
        
        Args:
            project_path: Path to the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Attempting to add project: {project_path}")
            project_path = os.path.abspath(project_path)
            
            # Check if project already exists
            if project_path in self.indexers:
                logger.warning(f"Project already being indexed: {project_path}")
                return False
            
            # Initialize indexer
            logger.info(f"Initializing Indexer for: {project_path}")
            indexer = Indexer(self.config_manager, project_path)
            logger.info(f"Successfully initialized Indexer for: {project_path}")
            self.indexers[project_path] = indexer

            # --- Combine ignore patterns for FileWatcher ---
            # Base patterns from root config
            base_ignore_patterns = self.config.get("indexer", {}).get("ignore_patterns", [])
            # Project patterns from .augmentoriumignore
            project_ignore_patterns = []
            project_ignore_file = self.config_manager.get_project_ignore_file_path(project_path)
            if os.path.exists(project_ignore_file):
                try:
                    with open(project_ignore_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                project_ignore_patterns.append(line)
                except Exception as e:
                    logger.warning(f"Failed to read project ignore file {project_ignore_file} for watcher: {e}")

            combined_patterns = list(set(base_ignore_patterns + project_ignore_patterns))
            # --- End Combine ignore patterns ---

            # Add to file watcher using combined patterns
            self.file_watcher.add_project(project_path)

            logger.info(f"Added project to index: {project_path} with {len(combined_patterns)} ignore patterns.")
            logger.info(f"Finished add_project for: {project_path}")
            
            # Perform initial indexing
            if self.running:
                threading.Thread(
                    target=indexer.full_index,
                    daemon=True
                ).start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to add project {project_path}: {e}")
            return False
    
    def remove_project(self, project_path: str) -> bool:
        """
        Remove a project from indexing
        
        Args:
            project_path: Path to the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        project_path = os.path.abspath(project_path)
        
        if project_path not in self.indexers:
            logger.warning(f"Project not being indexed: {project_path}")
            return False
        
        try:
            # Close resources
            try:
                self.indexers[project_path].close()
            except Exception:
                pass

            # Remove from indexers
            del self.indexers[project_path]
            
            # Remove from file watcher
            self.file_watcher.remove_project(project_path)
            
            logger.info(f"Removed project from index: {project_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove project {project_path}: {e}")
            return False
    
    def _handle_file_event(self, event: FileEvent) -> None:
        """
        Handle a file event
        
        Args:
            event: File event
        """
        try:
            # Get indexer for the project
            indexer = self.indexers.get(event.project_path)
            if not indexer:
                logger.warning(f"No indexer for project: {event.project_path}")
                return
            
            # Handle the event
            indexer.handle_file_event(event)
        except Exception as e:
            logger.error(f"Failed to handle file event {event}: {e}")
    
    def start(self) -> None:
        """Start the indexer service"""
        if self.running:
            logger.warning("Indexer service already running")
            return
        
        logger.info("Starting indexer service")
        
        # Start file watcher
        self.file_watcher.start()
        
        # Mark as running
        self.running = True
        
        # Start check thread
        self.check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.check_thread.start()

        # Start status reporting thread
        self.status_thread = threading.Thread(target=self._status_loop, daemon=True)
        self.status_thread.start()
        
        # Perform initial indexing for all projects
        for project_path, indexer in self.indexers.items():
            threading.Thread(
                target=indexer.full_index,
                daemon=True
            ).start()


    def _status_loop(self):
        """Send status updates to backend every 5 seconds"""
        import time as _time
        import requests as _requests
        import datetime as _datetime

        while self.running:
            try:
                projects_status = []
                for path, indexer in self.indexers.items():
                    import os as _os
                    def get_size(start_path):
                        total_size = 0
                        for dirpath, dirnames, filenames in _os.walk(start_path):
                            for f in filenames:
                                fp = _os.path.join(dirpath, f)
                                try:
                                    total_size += _os.path.getsize(fp)
                                except Exception:
                                    pass
                        return total_size

                    status = {
                        "name": indexer.project_name,
                        "path": path,
                        "status": indexer.status,
                        "lastIndexed": indexer.last_indexed,
                        "size": get_size(path),
                        "error": indexer.error
                    }
                    projects_status.append(status)

                payload = {
                    "indexer_id": "indexer-1",
                    "timestamp": _datetime.datetime.utcnow().isoformat() + "Z",
                    "projects": projects_status
                }

                # Send POST to backend API
                _requests.post("http://localhost:6655/api/indexer/status", json=payload, timeout=2)
            except Exception:
                pass  # Ignore errors for now

            _time.sleep(5)
    
    def _check_loop(self) -> None:
        """Check loop for periodic tasks"""
        import time as _time
        while self.running:
            try:
                # Reload config from disk to get latest projects list
                self.config_manager.reload() # This now reloads the single root config

                # Sync projects based on the reloaded config
                projects_in_config = self.config_manager.get_all_projects() # Gets projects from self.config
                logger.debug(f"[Indexer Check Loop] Reloaded config projects: {projects_in_config}")
                current_paths = set(self.indexers.keys())
                config_paths = set(projects_in_config.values())
                logger.debug(f"[Indexer Check Loop] Config paths (abs): {[os.path.abspath(p) for p in config_paths]}")
                logger.debug(f"[Indexer Check Loop] Current indexer paths (abs): {[os.path.abspath(p) for p in current_paths]}")

                logger.debug(f"[Indexer Check Loop] Current indexer paths: {current_paths}")
                logger.debug(f"[Indexer Check Loop] Config project paths: {config_paths} (type: {type(config_paths)})")

                new_projects = config_paths - current_paths
                logger.debug(f"[Indexer Check Loop] New projects to add: {new_projects} (type: {type(new_projects)})")
                
                # Additional debug logging
                logger.debug(f"[Indexer Check Loop] Current indexer paths details:")
                for path in current_paths:
                    logger.debug(f"- {path}")
                logger.debug(f"[Indexer Check Loop] Config project paths details:")
                for path in config_paths:
                    logger.debug(f"- {path}")

                # Add new projects
                for path in new_projects:
                    logger.info(f"Detected new project in config: {path}")
                    self.add_project(path)

                # Optionally, remove projects no longer in config
                # for path in current_paths - config_paths:
                #     logger.info(f"Removing project no longer in config: {path}")
                #     self.remove_project(path)

            except Exception as e:
                logger.error(f"Error in check loop: {e}")
            
            _time.sleep(15)
    
    def stop(self) -> None:
        """Stop the indexer service"""
        if not self.running:
            logger.warning("Indexer service not running")
            return
        
        logger.info("Stopping indexer service")
        
        # Stop file watcher
        self.file_watcher.stop()
        
        # Mark as not running
        self.running = False
        
        # Wait for check thread to exit
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(timeout=5.0)


def start_indexer(
    config: ConfigManager,
    project_paths: Optional[List[str]] = None
) -> IndexerService:
    """
    Start the indexer service
    
    Args:
        config: Configuration manager
        project_paths: List of project paths to index
    
    Returns:
        IndexerService: Indexer service
    """
    # Create indexer service
    service = IndexerService(config)
    
    # Add projects
    if project_paths:
        for path in project_paths:
            service.add_project(path)
    else:
        # Add all registered projects
        projects_dict = config.get_all_projects()
        if not projects_dict:
            projects_dict = {}
        for project_name, project_path in projects_dict.items():
            service.add_project(project_path)
    
    # Start service
    service.start()
    
# --- Flask API for pause/resume endpoints ---
from flask import Flask, jsonify

api_app = Flask("indexer_api")

@api_app.route("/pause", methods=["POST"])
def pause_indexer():
    global indexer_service_instance
    if indexer_service_instance is not None:
        indexer_service_instance.pause()
        return jsonify({"status": "paused"}), 200
    return jsonify({"error": "Indexer service not running"}), 500

@api_app.route("/resume", methods=["POST"])
def resume_indexer():
    global indexer_service_instance
    if indexer_service_instance is not None:
        indexer_service_instance.resume()
        return jsonify({"status": "resumed"}), 200
    return jsonify({"error": "Indexer service not running"}), 500
@api_app.route('/reindex', methods=['POST'])
def trigger_reindex():
    from flask import request, jsonify
    import threading
    global indexer_service_instance
    data = request.json
    project_name = data.get('project_name')
    if not project_name:
        return jsonify({"error": "Missing project_name"}), 400
    if indexer_service_instance is None:
        return jsonify({"error": "Indexer service not running"}), 500

    # Try to find the Indexer instance for the given project_name
    # Map project_name to project_path by matching Indexer.project_name
    target_indexer = None
    for idx in indexer_service_instance.indexers.values():
        if getattr(idx, "project_name", None) == project_name:
            target_indexer = idx
            break

    if not target_indexer:
        return jsonify({"error": f"Project '{project_name}' not found"}), 404

    def do_reindex():
        try:
            processed = target_indexer.full_index()
            logger.info(f"[API] Reindex completed for project: {project_name} ({processed} files processed)")
        except Exception as e:
            logger.error(f"[API] Reindex failed for project: {project_name}: {e}")

    threading.Thread(target=do_reindex, daemon=True).start()
    logger.info(f"[API] Reindex triggered for project: {project_name}")
    return jsonify({"status": "reindex triggered", "project": project_name})

# --- Entry point for starting indexer and API server ---
indexer_service_instance = None

def start_indexer(
    config: ConfigManager,
    project_paths: Optional[List[str]] = None
) -> IndexerService:
    """
    Start the indexer service
    
    Args:
        config: Configuration manager
        project_paths: List of project paths to index
    
    Returns:
        IndexerService: Indexer service
    """
    global indexer_service_instance
    # Create indexer service
    service = IndexerService(config)
    indexer_service_instance = service
    
    # Add projects
    if project_paths:
        for path in project_paths:
            service.add_project(path)
    else:
        # Add all registered projects
        projects_dict = config.get_all_projects()
        config.reload()
        projects_dict = config.get_all_projects()
        logger.info(f"DEBUG: get_all_projects() after reload returned: {projects_dict}")
        if not projects_dict:
            projects_dict = {}
        for project_name, project_path in projects_dict.items():
            service.add_project(project_path)
    
    # Start service
    service.start()

    # Start Flask API in a background thread
    import threading
    host = config.config.get("indexer", {}).get("host", "localhost")
    port = config.config.get("indexer", {}).get("port", 6656)
    threading.Thread(target=api_app.run, kwargs={"host": host, "port": port}, daemon=True).start()
    
    return service
    return service


def main():
    """Main entry point"""
    from config.manager import ConfigManager
    from utils.logging import setup_logging
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Augmentorium Indexer")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--projects", help="Comma-separated list of project paths to index")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Get project paths
    project_paths = args.projects.split(",") if args.projects else None
    
    # Start indexer
    service = start_indexer(config, project_paths)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping indexer service")
        service.stop()


if __name__ == "__main__":
    main()
