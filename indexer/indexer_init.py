"""
Indexer for Augmentorium
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from queue import Queue

from augmentorium.config.manager import ConfigManager
from augmentorium.utils.db_utils import VectorDB
from augmentorium.utils.logging import ProjectLogger
from augmentorium.indexer.watcher import FileWatcherService, FileEvent
from augmentorium.indexer.chunker import Chunker, CodeChunk
from augmentorium.indexer.embedder import OllamaEmbedder, ChunkEmbedder, ChunkProcessor

logger = logging.getLogger(__name__)

class Indexer:
    """Main indexer for Augmentorium"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        project_path: str
    ):
        """
        Initialize indexer
        
        Args:
            config_manager: Configuration manager
            project_path: Path to the project
        """
        self.config_manager = config_manager
        self.project_path = os.path.abspath(project_path)
        
        # Load project configuration
        self.project_config = config_manager.get_project_config(self.project_path)
        
        # Set up project logger
        self.project_name = self.project_config["project"]["name"]
        self.logger = ProjectLogger(self.project_name)
        
        # Set up vector database
        db_path = config_manager.get_db_path(self.project_path)
        self.vector_db = VectorDB(db_path)
        
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
        
        # Extract exclude patterns
        self.exclude_patterns = self.project_config["project"].get("exclude_patterns", [])
        
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
            self.logger.info(f"Processing file: {file_path}")
            
            # Chunk the file
            chunks = self.chunker.chunk_file(file_path)
            
            if not chunks:
                self.logger.warning(f"No chunks generated for file: {file_path}")
                return 0
            
            self.logger.info(f"Generated {len(chunks)} chunks for file: {file_path}")
            
            # Process chunks
            num_processed = self.chunk_processor.process_chunks(chunks, show_progress=False)
            
            self.logger.info(f"Processed {num_processed} chunks for file: {file_path}")
            
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
            self.logger.info(f"Starting full index for project: {self.project_name}")
            
            # Create file watcher to use its scanning functionality
            watcher = FileWatcherService()
            
            # Scan for files
            events = watcher.scan_project(self.project_path)
            
            # Filter out non-files and files matching exclude patterns
            file_events = [event for event in events if not event.is_directory]
            
            self.logger.info(f"Found {len(file_events)} files to index")
            
            # Process each file
            processed_count = 0
            for i, event in enumerate(file_events):
                self.logger.info(f"Indexing file {i+1}/{len(file_events)}: {event.relative_path}")
                self.handle_file_event(event)
                processed_count += 1
            
            self.logger.info(f"Full index completed for project: {self.project_name}")
            self.logger.info(f"Processed {processed_count} files")
            
            return processed_count
        except Exception as e:
            self.logger.error(f"Failed to perform full index: {e}")
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
            
            # Initialize indexer
            indexer = Indexer(self.config_manager, project_path)
            self.indexers[project_path] = indexer
            
            # Get project config
            project_config = self.config_manager.get_project_config(project_path)
            exclude_patterns = project_config["project"].get("exclude_patterns", [])
            
            # Add to file watcher
            self.file_watcher.add_project(project_path, exclude_patterns)
            
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
        
        # Perform initial indexing for all projects
        for project_path, indexer in self.indexers.items():
            threading.Thread(
                target=indexer.full_index,
                daemon=True
            ).start()
    
    def _check_loop(self) -> None:
        """Check loop for periodic tasks"""
        while self.running:
            try:
                # Perform periodic tasks here if needed
                pass
            except Exception as e:
                logger.error(f"Error in check loop: {e}")
            
            # Sleep for a while
            time.sleep(60)
    
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
    from augmentorium.config.manager import ConfigManager
    from augmentorium.utils.logging import setup_logging
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
