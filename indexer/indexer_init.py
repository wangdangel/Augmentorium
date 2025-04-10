"""
Indexer for Augmentorium
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from queue import Queue

from config.manager import ConfigManager
from utils.db_utils import VectorDB
from utils.logging import ProjectLogger
from utils.path_utils import get_path_hash_key # Import the missing function
from indexer.watcher import FileWatcherService, FileEvent, FileHasher
from indexer.chunker import Chunker, CodeChunk
from indexer.embedder import OllamaEmbedder, ChunkEmbedder, ChunkProcessor

logger = logging.getLogger(__name__)

class Indexer:
    """Main indexer for Augmentorium"""

    def close(self):
        """Close all resources"""
        try:
            # Close vector DB if it has a close method
            if hasattr(self.vector_db, "close"):
                self.vector_db.close()
        except Exception:
            pass
        # TODO: Close graph DB connections if persistent (currently opened per operation)
        # TODO: Stop any file watchers if running
        # Placeholder for future cleanup logic

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
        # Remove storing the service reference
        
        # Load project configuration
        self.project_config = config_manager.get_project_config(self.project_path)
        
        # Set up project logger
        self.project_name = self.project_config["project"]["name"]
        self.logger = ProjectLogger(self.project_name)
        
        # Set up vector database
        db_path = config_manager.get_db_path(self.project_path)
        self.vector_db = VectorDB(db_path)
        
        # Initialize graph database if needed
        try:
            graph_db_path = os.path.join(self.project_path, ".augmentorium", "code_graph.db")
            if not os.path.exists(graph_db_path):
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
                print(f"Graph database initialized at {graph_db_path}")
        except Exception as e:
            print(f"Failed to initialize graph database: {e}")
        
        # Set up Ollama embedder
        ollama_config = config_manager.global_config.get("ollama", {})
        self.ollama_embedder = OllamaEmbedder(
            base_url=ollama_config.get("base_url", "http://localhost:11434"),
            model=ollama_config.get("embedding_model", "codellama"),
            batch_size=ollama_config.get("embedding_batch_size", 10)
        )
        
        # Set up chunker
        self.chunker = Chunker(self.project_config.get("chunking", {}))
        
        # Set up chunk processor
        self.chunk_processor = ChunkProcessor(
            vector_db=self.vector_db,
            embedder=ChunkEmbedder(
                ollama_embedder=self.ollama_embedder,
                batch_size=ollama_config.get("embedding_batch_size", 10),
                max_workers=config_manager.global_config.get("indexer", {}).get("max_workers", 4)
            )
        )
        
        # Load ignore patterns from config.yaml
        import pathspec
        ignore_patterns = self.config_manager.global_config.get("indexer", {}).get("ignore_patterns", [])
        project_excludes = self.project_config["project"].get("exclude_patterns", [])
        combined_patterns = list(set(project_excludes + ignore_patterns))
        self.ignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", combined_patterns)
        
        # Initialize file hasher and load cache
        cache_dir = os.path.join(
            config_manager.global_config["general"]["log_dir"],
            "cache"
        )
        os.makedirs(cache_dir, exist_ok=True)
        project_hash = ""
        try:
            import hashlib
            project_hash = hashlib.md5(self.project_path.encode()).hexdigest()
        except Exception:
            pass
        self.hash_cache_file = os.path.join(cache_dir, f"{project_hash}_hash_cache.json")
        self.file_hasher = FileHasher()
        self.file_hasher.load_cache(self.hash_cache_file)
        
        self.logger.info(f"Initialized indexer for project: {self.project_name}")
    
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

                graph_db_path = os.path.join(self.project_path, ".augmentorium", "code_graph.db")
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
                        # ref can be a symbol name or ID; here we store as-is
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
        
        # Initialize projects
        self.indexers: Dict[str, Indexer] = {}
        
        # Initialize file watcher
        indexer_config = config_manager.global_config.get("indexer", {})
        cache_dir = os.path.join(
            config_manager.global_config["general"]["log_dir"],
            "cache"
        )
        
        self.file_watcher = FileWatcherService(
            polling_interval=indexer_config.get("polling_interval", 1.0),
            hash_algorithm=indexer_config.get("hash_algorithm", "md5"),
            cache_dir=cache_dir,
            event_callback=self._handle_file_event
        )
        
        self.running = False
        self.check_thread = None
        
        logger.info("Initialized indexer service")
    
    def add_project(self, project_path: str) -> bool:
        """
        Add a project to index
        
        Args:
            project_path: Path to the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project_path = os.path.abspath(project_path)
            
            # Check if project already exists
            if project_path in self.indexers:
                logger.warning(f"Project already being indexed: {project_path}")
                return False
            
            # Initialize indexer (no longer passing file_watcher_service)
            indexer = Indexer(self.config_manager, project_path)
            self.indexers[project_path] = indexer

            # Get project config for combined patterns
            project_config = self.config_manager.get_project_config(project_path)
            
            # Combine global and project-specific ignore patterns
            global_ignore_patterns = self.config_manager.global_config.get("indexer", {}).get("ignore_patterns", [])
            project_excludes = project_config["project"].get("exclude_patterns", [])
            combined_patterns = list(set(project_excludes + global_ignore_patterns))
            
            # Add to file watcher using combined patterns
            self.file_watcher.add_project(project_path, combined_patterns)
            
            logger.info(f"Added project to index: {project_path}")
            
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
                _requests.post("http://localhost:6655/api/indexer_status", json=payload, timeout=2)
            except Exception:
                pass  # Ignore errors for now

            _time.sleep(5)
    
    def _check_loop(self) -> None:
        """Check loop for periodic tasks"""
        import time as _time
        while self.running:
            try:
                # Reload config from disk to get latest projects
                self.config_manager.reload()

                # Reload config and sync projects every 15 seconds
                projects_in_config = self.config_manager.get_all_projects()
                current_paths = set(self.indexers.keys())
                config_paths = set(projects_in_config.values())

                logger.debug(f"[Indexer Check Loop] Current indexer paths: {current_paths}")
                logger.debug(f"[Indexer Check Loop] Config project paths: {config_paths}")

                new_projects = config_paths - current_paths
                logger.debug(f"[Indexer Check Loop] New projects to add: {new_projects}")

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
        for project_name, project_path in config.get_all_projects().items():
            service.add_project(project_path)
    
    # Start service
    service.start()
    
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
