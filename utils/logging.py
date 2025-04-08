"""
Logging utilities for Augmentorium
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional

from augmentorium.config.defaults import DEFAULT_LOG_DIR

def setup_logging(level: int = logging.INFO, log_dir: Optional[str] = None) -> None:
    """
    Set up logging configuration
    
    Args:
        level: Logging level
        log_dir: Directory for log files (uses default if None)
    """
    # Use default log directory if not specified
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Create rotating file handler
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"augmentorium_{today}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Create Augmentorium logger
    logger = logging.getLogger("augmentorium")
    logger.info(f"Logging initialized at level {logging.getLevelName(level)}")

class ProjectLogger:
    """Logger for project-specific operations"""
    
    def __init__(self, project_name: str, log_dir: Optional[str] = None, level: int = logging.INFO):
        """
        Initialize a project-specific logger
        
        Args:
            project_name: Name of the project
            log_dir: Directory for log files (uses default if None)
            level: Logging level
        """
        self.project_name = project_name
        
        # Use default log directory if not specified
        if log_dir is None:
            log_dir = DEFAULT_LOG_DIR
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create logger for this project
        self.logger = logging.getLogger(f"augmentorium.project.{project_name}")
        self.logger.setLevel(level)
        
        # Remove existing handlers if any
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create project-specific file handler
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"project_{project_name}_{today}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Add handler
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"Project logger initialized for {project_name}")
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message"""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message"""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message"""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a critical message"""
        self.logger.critical(msg, *args, **kwargs)
