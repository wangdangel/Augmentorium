"""
ProjectWatcher: Watches a single project for file changes.
Moved from indexer/watcher.py as part of modular refactor.
"""

import os
import logging
from typing import Optional, List
from queue import Queue
from watchdog.observers import Observer

from utils.path_utils import normalize_path
from indexer.file_hasher import FileHasher
from indexer.event_handler import ProjectEventHandler

logger = logging.getLogger(__name__)

class ProjectWatcher:
    """Watcher for a single project"""
    
    def __init__(
        self,
        project_path: str,
        event_queue: Queue,
        exclude_patterns: Optional[List[str]] = None,
        polling_interval: float = 1.0,
        hash_algorithm: str = "md5",
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the project watcher
        
        Args:
            project_path: Path to the project
            event_queue: Queue for events
            exclude_patterns: Patterns to exclude
            polling_interval: Interval for polling (seconds)
            hash_algorithm: Hash algorithm for file change detection
            cache_dir: Directory for hash cache
        """
        self.project_path = normalize_path(project_path)
        self.event_queue = event_queue
        self.exclude_patterns = exclude_patterns or []
        self.polling_interval = polling_interval
        
        # Initialize file hasher
        self.file_hasher = FileHasher(algorithm=hash_algorithm)
        
        # Set up hash cache
        if cache_dir:
            self.cache_file = os.path.join(cache_dir, "hash_cache.json")
            self.file_hasher.load_cache(self.cache_file)
        else:
            self.cache_file = None
        
        # Initialize observer and handler
        self.observer = Observer()
        self.handler = ProjectEventHandler(
            project_path=self.project_path,
            event_queue=self.event_queue,
            exclude_patterns=self.exclude_patterns,
            file_hasher=self.file_hasher
        )
        
        # Register for both realtime and filesystem polling for reliability
        self.observer.schedule(self.handler, self.project_path, recursive=True)
        
        logger.info(f"Initialized watcher for project: {self.project_path}")
    
    def start(self) -> None:
        """Start the watcher"""
        logger.info(f"Starting watcher for project: {self.project_path}")
        self.observer.start()
    
    def stop(self) -> None:
        """Stop the watcher"""
        logger.info(f"Stopping watcher for project: {self.project_path}")
        self.observer.stop()
        
        # Save hash cache
        if self.cache_file:
            self.file_hasher.save_cache(self.cache_file)
    
    def join(self, timeout: Optional[float] = None) -> None:
        """Join the watcher thread"""
        self.observer.join(timeout=timeout)