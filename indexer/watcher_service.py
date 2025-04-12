"""
FileWatcherService: Service for watching multiple projects.
Moved from indexer/watcher.py as part of modular refactor.
"""

import os
import threading
import logging
from typing import Callable, Dict, Optional, List
from queue import Queue
import pathspec

from utils.path_utils import normalize_path
from indexer.file_event import FileEvent
from indexer.project_watcher import ProjectWatcher

logger = logging.getLogger(__name__)

class FileWatcherService:
    """Service for watching multiple projects"""
    
    def __init__(
        self,
        config_manager,
        polling_interval: float = 1.0,
        hash_algorithm: str = "md5",
        cache_dir: Optional[str] = None,
        event_callback: Optional[Callable[[FileEvent], None]] = None
    ):
        """
        Initialize the file watcher service
        
        Args:
            config_manager: ConfigManager instance
            polling_interval: Interval for polling (seconds)
            hash_algorithm: Hash algorithm for file change detection
            cache_dir: Directory for hash cache
            event_callback: Callback for file events
        """
        self.config_manager = config_manager
        self.polling_interval = polling_interval
        self.hash_algorithm = hash_algorithm
        self.cache_dir = cache_dir
        self.event_callback = event_callback
        
        # Create cache directory
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize projects
        self.projects: Dict[str, ProjectWatcher] = {}
        
        # Create event queue and processor thread
        self.event_queue: Queue = Queue()
        self.running = False
        self.processor_thread = threading.Thread(target=self._process_events)
        
        logger.info("Initialized file watcher service")
    
    def add_project(
        self,
        project_path: str
    ) -> bool:
        """
        Add a project to watch
        
        Args:
            project_path: Path to the project
            (removed) exclude_patterns: Patterns to exclude
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project_path = normalize_path(project_path)
            
            # Check if project already exists
            if project_path in self.projects:
                logger.warning(f"Project already being watched: {project_path}")
                return False
            
            # Check if directory exists
            if not os.path.isdir(project_path):
                logger.error(f"Project directory does not exist: {project_path}")
                return False
            
            # Create project cache directory
            project_cache_dir = None
            if self.cache_dir:
                import hashlib
                project_hash = hashlib.md5(project_path.encode()).hexdigest()
                project_cache_dir = os.path.join(self.cache_dir, project_hash)
                os.makedirs(project_cache_dir, exist_ok=True)
            
            # Create watcher
            watcher = ProjectWatcher(
                project_path=project_path,
                event_queue=self.event_queue,
                config_manager=self.config_manager,
                polling_interval=self.polling_interval,
                hash_algorithm=self.hash_algorithm,
                cache_dir=project_cache_dir
            )
            
            # Start watcher if service is running
            if self.running:
                watcher.start()
            
            # Add to projects
            self.projects[project_path] = watcher
            
            logger.info(f"Added project to watch: {project_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to add project {project_path}: {e}")
            return False
    
    def remove_project(self, project_path: str) -> bool:
        """
        Remove a project from watching
        
        Args:
            project_path: Path to the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        project_path = normalize_path(project_path)
        
        if project_path not in self.projects:
            logger.warning(f"Project not being watched: {project_path}")
            return False
        
        try:
            # Stop watcher
            watcher = self.projects[project_path]
            watcher.stop()
            watcher.join()
            
            # Remove from projects
            del self.projects[project_path]
            
            logger.info(f"Removed project from watch: {project_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove project {project_path}: {e}")
            return False
    
    def _process_events(self) -> None:
        """Process events from the queue"""
        while self.running:
            try:
                # Get event from queue with timeout
                event = self.event_queue.get(timeout=1.0)
                
                # Process event
                if self.event_callback:
                    self.event_callback(event)
                
                # Mark as done
                self.event_queue.task_done()
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    break
    
    def start(self) -> None:
        """Start the service"""
        if self.running:
            logger.warning("File watcher service already running")
            return
        
        logger.info("Starting file watcher service")
        
        # Start processor thread
        self.running = True
        self.processor_thread = threading.Thread(target=self._process_events)
        self.processor_thread.daemon = True
        self.processor_thread.start()
        
        # Start all project watchers
        for watcher in self.projects.values():
            watcher.start()
    
    def stop(self) -> None:
        """Stop the service"""
        if not self.running:
            logger.warning("File watcher service not running")
            return
        
        logger.info("Stopping file watcher service")
        
        # Stop processor thread
        self.running = False
        if self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5.0)
        
        # Stop all project watchers
        for watcher in self.projects.values():
            watcher.stop()
            watcher.join()

    @staticmethod
    def scan_project(project_path: str, ignore_spec: pathspec.PathSpec) -> List[FileEvent]:
        """
        Scan a project for initial indexing using a provided ignore spec.

        Args:
            project_path: Path to the project
            ignore_spec: Compiled pathspec object for exclusions

        Returns:
            List[FileEvent]: List of file events
        """
        project_path = normalize_path(project_path)
        events = []

        # Check if project exists
        if not os.path.isdir(project_path):
            logger.error(f"Project directory does not exist: {project_path}")
            return events

        # Ensure ignore_spec is valid
        if not ignore_spec:
            logger.error(f"Invalid ignore_spec provided for project {project_path} scan.")
            ignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", [])

        # Walk directory
        for root, dirs, files in os.walk(project_path):
            # Apply ignore_spec to directories
            dirs_to_remove = []
            from utils.ignore_utils import should_ignore
            for d in dirs:
                dir_path = os.path.join(root, d)
                if should_ignore(dir_path, project_path, ignore_spec):
                    logger.debug(f"Skipping directory (ignore spec match): {os.path.relpath(dir_path, project_path)}")
                    dirs_to_remove.append(d)
                else:
                    logger.debug(f"Including directory: {os.path.relpath(dir_path, project_path)}")
            for d in dirs_to_remove:
                dirs.remove(d)

            # Process files
            for file in files:
                file_path = os.path.join(root, file)
                from utils.ignore_utils import should_ignore
                if should_ignore(file_path, project_path, ignore_spec):
                    logger.debug(f"Skipping file (ignore spec match): {os.path.relpath(file_path, project_path)}")
                    continue
                else:
                    logger.debug(f"Including file: {os.path.relpath(file_path, project_path)}")
                events.append(FileEvent(
                    event_type="created",
                    file_path=file_path,
                    is_directory=False,
                    project_path=project_path
                ))
        return events