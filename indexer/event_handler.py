"""
ProjectEventHandler: Event handler for project file changes.
Moved from indexer/watcher.py as part of modular refactor.
"""

import logging
import pathspec
from typing import Optional, List
from queue import Queue
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from utils.path_utils import normalize_path, get_relative_path
from indexer.file_hasher import FileHasher
from indexer.file_event import FileEvent

logger = logging.getLogger(__name__)

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
        self.ignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", self.exclude_patterns)
    
    def _should_exclude(self, path: str) -> bool:
        """
        Check if a path should be excluded
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path should be excluded, False otherwise
        """
        rel_path = get_relative_path(path, self.project_path)
        return self.ignore_spec.match_file(rel_path)
    
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