"""
ProjectEventHandler: Event handler for project file changes.
Moved from indexer/watcher.py as part of modular refactor.
"""

import logging
import pathspec
from typing import Optional
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
        config_manager,
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
        from utils.ignore_utils import get_ignore_spec
        self.project_path = normalize_path(project_path)
        self.event_queue = event_queue
        self.config_manager = config_manager
        self.file_hasher = file_hasher or FileHasher()
        self.ignore_spec = get_ignore_spec(self.config_manager, self.project_path)
    
    def _should_exclude(self, path: str) -> bool:
        """
        Deprecated: Use should_ignore from utils.ignore_utils instead.
        """
        from utils.ignore_utils import should_ignore
        return should_ignore(path, self.project_path, self.ignore_spec)
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events"""
        from utils.ignore_utils import should_ignore
        if should_ignore(event.src_path, self.project_path, self.ignore_spec):
            return
        
        self.event_queue.put(FileEvent(
            event_type="created",
            file_path=event.src_path,
            is_directory=event.is_directory,
            project_path=self.project_path
        ))
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events"""
        from utils.ignore_utils import should_ignore
        if should_ignore(event.src_path, self.project_path, self.ignore_spec) or event.is_directory:
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
        from utils.ignore_utils import should_ignore
        if should_ignore(event.src_path, self.project_path, self.ignore_spec):
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
        from utils.ignore_utils import should_ignore
        src_excluded = should_ignore(event.src_path, self.project_path, self.ignore_spec)
        dest_excluded = should_ignore(event.dest_path, self.project_path, self.ignore_spec)
        
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