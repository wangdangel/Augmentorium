"""
FileEvent: Data structure for file system events.
Moved from indexer/watcher.py as part of modular refactor.
"""

import time
from utils.path_utils import normalize_path, get_relative_path

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