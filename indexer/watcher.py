"""
File system watcher for Augmentorium
"""

import os
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Callable
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from augmentorium.utils.path_utils import (
    normalize_path,
    get_relative_path,
    matches_any_pattern,
    get_path_hash_key,
)

logger = logging.getLogger(__name__)

class FileHasher:
    """Utility for tracking file changes via hashing"""
    
    def __init__(self, algorithm: str = "md5"):
        """
        Initialize the file hasher
        
        Args:
            algorithm: Hash algorithm to use
        """
        self.algorithm = algorithm
        self.hash_cache: Dict[str, str] = {}
    
    def compute_hash(self, file_path: str) -> Optional[str]:
        """
        Compute the hash of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[str]: Hash of the file contents, or None if error
        """
        try:
            hasher = hashlib.new(self.algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute hash for {file_path}: {e}")
            return None
    
    def has_changed(self, file_path: str) -> bool:
        """
        Check if a file has changed since the last check
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if the file has changed or is new, False otherwise
        """
        # Normalize path for consistent key
        key = get_path_hash_key(file_path)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            if key in self.hash_cache:
                del self.hash_cache[key]
            return False
        
        # Compute new hash
        new_hash = self.compute_hash(file_path)
        if new_hash is None:
            return False
        
        # Check if hash has changed
        old_hash = self.hash_cache.get(key)
        has_changed = old_hash != new_hash
        
        # Update hash cache
        self.hash_cache[key] = new_hash
        
        return has_changed
    
    def update_hash(self, file_path: str) -> None:
        """
        Update the hash cache for a file
        
        Args:
            file_path: Path to the file
        """
        key = get_path_hash_key(file_path)
        new_hash = self.compute_hash(file_path)
        if new_hash:
            self.hash_cache[key] = new_hash
    
    def remove_hash(self, file_path: str) -> None:
        """
        Remove a file from the hash cache
        
        Args:
            file_path: Path to the file
        """
        key = get_path_hash_key(file_path)
        if key in self.hash_cache:
            del self.hash_cache[key]
    
    def load_cache(self, cache_file: str) -> bool:
        """
        Load hash cache from file
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(cache_file):
                return False
            
            with open(cache_file, "r") as f:
                self.hash_cache = json.loads(f.read())
            
            return True
        except Exception as e:
            logger.error(f"Failed to load hash cache from {cache_file}: {e}")
            return False
    
    def save_cache(self, cache_file: str) -> bool:
        """
        Save hash cache to file
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            with open(cache_file, "w") as f:
                f.write(json.dumps(self.hash_cache))
            
            return True
        except Exception as e:
            logger.error(f"Failed to save hash cache to {cache_file}: {e}")
            return False


class FileEvent:
    """File event data structure"""
    
    def __init__(
        self,
        event_type: str,
        file_path: str,
        is_directory: bool,
        project_path: str
    ):
        """
        Initialize a file event
        
        Args:
            event_type: Type of event ("created", "modified", "deleted", "moved")
            file_path: Path to the file
            is_directory: Whether the path is a directory
            project_path: Path to the project
        """
        self.event_type = event_type
        self.file_path = normalize_path(file_path)
        self.is_directory = is_directory
        self.project_path = normalize_path(project_path)
        self.relative_path = get_relative_path(self.file_path, self.project_path)
        self.timestamp = time.time()
    
    def __str__(self) -> str:
        return f"FileEvent({self.event_type}, {self.relative_path})"


class ProjectEventHandler(FileSystemEventHandler):
    """Event handler for project file changes"""
    
    def __init__(
        self,
        project_path: str,
        event_queue: Queue,
        exclude_patterns: Optional[List[str]] = None,
        file_hasher: Optional[FileHasher] = None
    ):
        """
        Initialize the event handler
        
        Args:
            project_path: Path to the project
            event_queue: Queue for events
            exclude_patterns: Patterns to exclude
            file_hasher: Optional file hasher for tracking changes
        """
        self.project_path = normalize_path(project_path)
        self.event_queue = event_queue
        self.exclude_patterns = exclude_patterns or []
        self.file_hasher = file_hasher or FileHasher()
        
        # Add default exclude patterns for the Augmentorium directory
        self.exclude_patterns.append("**/.augmentorium/**")
    
    def _should_exclude(self, path: str) -> bool:
        """
        Check if a path should be excluded
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path should be excluded, False otherwise
        """
        rel_path = get_relative_path(path, self.project_path)
        return matches_any_pattern(rel_path, self.exclude_patterns)
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events"""
        if self._should_exclude(event.src_path):
            return
        
        self.event_queue.put(FileEvent(
            event_type="created",
            file_path=event.src_path,
            is_directory=event.is_directory,
            project_path=self.project_path
        ))
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events"""
        if self._should_exclude(event.src_path) or event.is_directory:
            return
        
        # Only process if file content has actually changed
        if self.file_hasher and not self.file_hasher.has_changed(event.src_path):
            return
        
        self.event_queue.put(FileEvent(
            event_type="modified",
            file_path=event.src_path,
            is_directory=event.is_directory,
            project_path=self.project_path
        ))
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events"""
        if self._should_exclude(event.src_path):
            return
        
        # Remove from hash cache if using hasher
        if self.file_hasher:
            self.file_hasher.remove_hash(event.src_path)
        
        self.event_queue.put(FileEvent(
            event_type="deleted",
            file_path=event.src_path,
            is_directory=event.is_directory,
            project_path=self.project_path
        ))
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events"""
        # Check source path
        src_excluded = self._should_exclude(event.src_path)
        
        # Check destination path
        dest_excluded = self._should_exclude(event.dest_path)
        
        # Handle different cases
        if src_excluded and dest_excluded:
            # Both excluded, ignore
            return
        elif src_excluded and not dest_excluded:
            # Moved from excluded to included, treat as created
            self.event_queue.put(FileEvent(
                event_type="created",
                file_path=event.dest_path,
                is_directory=event.is_directory,
                project_path=self.project_path
            ))
        elif not src_excluded and dest_excluded:
            # Moved from included to excluded, treat as deleted
            self.event_queue.put(FileEvent(
                event_type="deleted",
                file_path=event.src_path,
                is_directory=event.is_directory,
                project_path=self.project_path
            ))
        else:
            # Both included, treat as moved
            self.event_queue.put(FileEvent(
                event_type="deleted",
                file_path=event.src_path,
                is_directory=event.is_directory,
                project_path=self.project_path
            ))
            self.event_queue.put(FileEvent(
                event_type="created",
                file_path=event.dest_path,
                is_directory=event.is_directory,
                project_path=self.project_path
            ))
            
            # Update hash cache if using hasher
            if self.file_hasher:
                self.file_hasher.remove_hash(event.src_path)
                self.file_hasher.update_hash(event.dest_path)


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


class FileWatcherService:
    """Service for watching multiple projects"""
    
    def __init__(
        self,
        polling_interval: float = 1.0,
        hash_algorithm: str = "md5",
        cache_dir: Optional[str] = None,
        event_callback: Optional[Callable[[FileEvent], None]] = None
    ):
        """
        Initialize the file watcher service
        
        Args:
            polling_interval: Interval for polling (seconds)
            hash_algorithm: Hash algorithm for file change detection
            cache_dir: Directory for hash cache
            event_callback: Callback for file events
        """
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
        self.event_queue: Queue[FileEvent] = Queue()
        self.running = False
        self.processor_thread = threading.Thread(target=self._process_events)
        
        logger.info("Initialized file watcher service")
    
    def add_project(
        self,
        project_path: str,
        exclude_patterns: Optional[List[str]] = None
    ) -> bool:
        """
        Add a project to watch
        
        Args:
            project_path: Path to the project
            exclude_patterns: Patterns to exclude
            
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
                project_hash = hashlib.md5(project_path.encode()).hexdigest()
                project_cache_dir = os.path.join(self.cache_dir, project_hash)
                os.makedirs(project_cache_dir, exist_ok=True)
            
            # Create watcher
            watcher = ProjectWatcher(
                project_path=project_path,
                event_queue=self.event_queue,
                exclude_patterns=exclude_patterns,
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
    
    def scan_project(self, project_path: str) -> List[FileEvent]:
        """
        Scan a project for initial indexing
        
        Args:
            project_path: Path to the project
            
        Returns:
            List[FileEvent]: List of file events
        """
        project_path = normalize_path(project_path)
        events = []
        
        # Check if project exists
        if not os.path.isdir(project_path):
            logger.error(f"Project directory does not exist: {project_path}")
            return events
        
        # Get watcher for exclude patterns
        watcher = self.projects.get(project_path)
        exclude_patterns = watcher.exclude_patterns if watcher else []
        
        # Walk directory
        for root, dirs, files in os.walk(project_path):
            # Apply exclude patterns to directories
            dirs_to_remove = []
            for d in dirs:
                dir_path = os.path.join(root, d)
                rel_path = get_relative_path(dir_path, project_path)
                if matches_any_pattern(rel_path, exclude_patterns):
                    dirs_to_remove.append(d)
            
            for d in dirs_to_remove:
                dirs.remove(d)
            
            # Process files
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = get_relative_path(file_path, project_path)
                
                # Skip excluded files
                if matches_any_pattern(rel_path, exclude_patterns):
                    continue
                
                # Create event
                events.append(FileEvent(
                    event_type="created",
                    file_path=file_path,
                    is_directory=False,
                    project_path=project_path
                ))
        
        return events
