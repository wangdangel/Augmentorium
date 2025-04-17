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
        import os
        rel_path = os.path.relpath(event.src_path, self.project_path)
        if rel_path.startswith('.Augmentorium') or should_ignore(event.src_path, self.project_path, self.ignore_spec) or event.is_directory:
            return
        logger.info(f"[RAW EVENT] CREATED: {event.src_path} (dir={event.is_directory})")
        self.event_queue.put(FileEvent(
            event_type="created",
            file_path=event.src_path,
            is_directory=event.is_directory,
            project_path=self.project_path
        ))
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events"""
        # Only log user-relevant files (not .Augmentorium or its subdirs)
        from utils.ignore_utils import should_ignore
        import os
        rel_path = os.path.relpath(event.src_path, self.project_path)
        if rel_path.startswith('.Augmentorium') or should_ignore(event.src_path, self.project_path, self.ignore_spec) or event.is_directory:
            return
        logger.info(f"[RAW EVENT] MODIFIED: {event.src_path} (dir={event.is_directory})")
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
        import os
        rel_path = os.path.relpath(event.src_path, self.project_path)
        if rel_path.startswith('.Augmentorium') or should_ignore(event.src_path, self.project_path, self.ignore_spec) or event.is_directory:
            return
        logger.info(f"[RAW EVENT] DELETED: {event.src_path} (dir={event.is_directory})")
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
        from utils.ignore_utils import should_ignore
        import os
        rel_src = os.path.relpath(event.src_path, self.project_path)
        rel_dest = os.path.relpath(getattr(event, 'dest_path', ''), self.project_path)
        src_excluded = rel_src.startswith('.Augmentorium') or should_ignore(event.src_path, self.project_path, self.ignore_spec)
        dest_excluded = rel_dest.startswith('.Augmentorium') or should_ignore(getattr(event, 'dest_path', ''), self.project_path, self.ignore_spec)
        if src_excluded and dest_excluded:
            return
        logger.info(f"[RAW EVENT] MOVED: {event.src_path} -> {getattr(event, 'dest_path', None)} (dir={event.is_directory})")
        if src_excluded and not dest_excluded:
            self.event_queue.put(FileEvent(
                event_type="created",
                file_path=event.dest_path,
                is_directory=event.is_directory,
                project_path=self.project_path
            ))
        elif not src_excluded and dest_excluded:
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
            if hasattr(event, 'dest_path'):
                self.file_hasher.update_hash(event.dest_path)