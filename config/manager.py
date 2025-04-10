"""
Configuration manager for Augmentorium
"""

import os
import yaml
import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Any

from config.defaults import (
    DEFAULT_GLOBAL_CONFIG,
    DEFAULT_PROJECT_CONFIG,
    GLOBAL_CONFIG_DIR,
    PROJECT_CONFIG_DIR,
)

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manager for global and project-specific configurations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Optional path to a configuration file
        """
        # Initialize with defaults
        self.global_config = deepcopy(DEFAULT_GLOBAL_CONFIG)
        self.global_config_path = os.path.join(GLOBAL_CONFIG_DIR, "global_config.yaml")

        # Always ensure global config dir exists
        self._ensure_global_config_dir()

        # Determine effective config file
        effective_config_path = None

        if config_path and os.path.exists(config_path):
            effective_config_path = config_path
        else:
            # Check for config.yaml relative to current working directory
            if os.path.exists("config.yaml"):
                effective_config_path = "config.yaml"

        if effective_config_path:
            try:
                with open(effective_config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self.global_config = loaded_config  # REPLACE global config entirely
                        logger.info(f"Loaded configuration from {effective_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {effective_config_path}: {e}")
        else:
            # Fallback: load global config file if it exists
            self._load_global_config()

        # Initialize project registry inside global config
        if "projects" not in self.global_config:
            self.global_config["projects"] = {}

        self.projects = self.global_config["projects"]
    
    def _ensure_global_config_dir(self) -> None:
        """Ensure global configuration directory exists"""
        os.makedirs(GLOBAL_CONFIG_DIR, exist_ok=True)
        os.makedirs(self.global_config["general"]["log_dir"], exist_ok=True)
    
    def _load_global_config(self) -> None:
        """Load global configuration from file if it exists"""
        if os.path.exists(self.global_config_path):
            try:
                with open(self.global_config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self._deep_update(self.global_config, loaded_config)
            except Exception as e:
                logger.warning(f"Failed to load global config: {e}")
        else:
            # Create default global config
            self._save_global_config()
    
    def _save_global_config(self) -> None:
        """Save global configuration to file"""
        try:
            with open(self.global_config_path, 'w') as f:
                yaml.dump(self.global_config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Failed to save global config: {e}")
    
    def _load_specific_config(self, config_path: str) -> None:
        """Load configuration from a specific file"""
        try:
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config:
                    self._deep_update(self.global_config, loaded_config)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
    
    def add_project(self, project_path: str, project_name: Optional[str] = None) -> bool:
        """
        Add a project to the registry
        
        Args:
            project_path: Path to the project
            project_name: Optional name for the project (defaults to directory name)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            abs_path = os.path.abspath(project_path)
            if not os.path.exists(abs_path):
                logger.error(f"Project path does not exist: {abs_path}")
                return False
            
            # Use directory name as project name if not provided
            if not project_name:
                project_name = os.path.basename(abs_path)
            
            # Add to projects registry inside global config
            self.projects[project_name] = abs_path
            self._save_global_config()
            
            return True
        except Exception as e:
            logger.error(f"Failed to add project: {e}")
            return False

    def remove_project(self, project_name: str) -> bool:
        """
        Remove a project from the registry
        
        Args:
            project_name: Name of the project to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if project_name in self.projects:
            del self.projects[project_name]
            self._save_global_config()
            return True
        return False
    
    def get_project_path(self, project_name: str) -> Optional[str]:
        """
        Get the path for a project
        
        Args:
            project_name: Name of the project
            
        Returns:
            str: Path to the project, or None if not found
        """
        return self.projects.get(project_name)
    
    def get_all_projects(self) -> Dict[str, str]:
        """
        Get all registered projects
        
        Returns:
            Dict[str, str]: Dictionary of project names to paths
        """
        return self.projects
    
    def get_project_config(self, project_path: str) -> Dict[str, Any]:
        """
        Get configuration for a specific project
        
        Args:
            project_path: Path to the project
            
        Returns:
            Dict: Project configuration
        """
        project_config = deepcopy(DEFAULT_PROJECT_CONFIG)
        
        # Path to project config file
        config_path = os.path.join(project_path, PROJECT_CONFIG_DIR, "config.yaml")
        
        # Load project config if it exists
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self._deep_update(project_config, loaded_config)
            except Exception as e:
                logger.warning(f"Failed to load project config: {e}")
        
        return project_config
    
    def save_project_config(self, project_path: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration for a specific project
        
        Args:
            project_path: Path to the project
            config: Configuration to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure project config directory exists
            config_dir = os.path.join(project_path, PROJECT_CONFIG_DIR)
            os.makedirs(config_dir, exist_ok=True)
            
            # Path to project config file
            config_path = os.path.join(config_dir, "config.yaml")
            
            # Save project config
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save project config: {e}")
            return False
    
    def initialize_project(self, project_path: str, project_name: Optional[str] = None) -> bool:
        """
        Initialize a new project
        
        Args:
            project_path: Path to the project
            project_name: Optional name for the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            abs_path = os.path.abspath(project_path)
            
            # Create project directory if it doesn't exist
            os.makedirs(abs_path, exist_ok=True)
            
            # Create project config directory
            config_dir = os.path.join(abs_path, PROJECT_CONFIG_DIR)
            os.makedirs(config_dir, exist_ok=True)
            
            # Create subdirectories
            os.makedirs(os.path.join(config_dir, "chroma"), exist_ok=True)
            os.makedirs(os.path.join(config_dir, "cache"), exist_ok=True)
            os.makedirs(os.path.join(config_dir, "metadata"), exist_ok=True)
            
            # Create default project config
            project_config = deepcopy(DEFAULT_PROJECT_CONFIG)
            
            # Use directory name as project name if not provided
            if not project_name:
                project_name = os.path.basename(abs_path)
            
            project_config["project"]["name"] = project_name
            
            # Save project config
            config_path = os.path.join(config_dir, "config.yaml")
            with open(config_path, 'w') as f:
                yaml.dump(project_config, f, default_flow_style=False)
            
            # Add to projects registry
            self.add_project(abs_path, project_name)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize project: {e}")
            return False
    
    def get_db_path(self, project_path: str) -> str:
        """
        Get the path to the project's vector database
        
        Args:
            project_path: Path to the project
            
        Returns:
            str: Path to the vector database
        """
        return os.path.join(project_path, PROJECT_CONFIG_DIR, "chroma")
    
    def get_cache_path(self, project_path: str) -> str:
        """
        Get the path to the project's cache directory
        
        Args:
            project_path: Path to the project
            
        Returns:
            str: Path to the cache directory
        """
        return os.path.join(project_path, PROJECT_CONFIG_DIR, "cache")
    
    def get_metadata_path(self, project_path: str) -> str:
        """
        Get the path to the project's metadata directory
        
        Args:
            project_path: Path to the project
            
        Returns:
            str: Path to the metadata directory
        """
        return os.path.join(project_path, PROJECT_CONFIG_DIR, "metadata")
    
    @staticmethod
    def _deep_update(d: Dict, u: Dict) -> Dict:
        """
        Recursively update a dictionary
        
        Args:
            d: Dictionary to update
            u: Dictionary with updates
            
        Returns:
            Dict: Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                ConfigManager._deep_update(d[k], v)
            else:
                d[k] = v
        return d
