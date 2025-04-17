"""
Configuration manager for Augmentorium
"""

import os
import yaml
import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Any

import os
import yaml
import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import necessary for graph DB initialization
from utils.graph_db import initialize_graph_db

from config.defaults import (
    DEFAULT_CONFIG,
    PROJECT_INTERNAL_DIR_NAME,
    DEFAULT_LOG_DIR # Keep for fallback log dir creation
)

logger = logging.getLogger(__name__)

# Define the root config file path (relative to where the script is run from)
# Assuming this manager is used from the root directory 'k:/Documents/augmentorium'
import os
ROOT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")

# Default content for the project-specific ignore file
DEFAULT_IGNORE_CONTENT = """# Folders and files to ignore for vector database indexing.
# Add one pattern per line. Uses gitignore syntax.
# Example:
# *.log
# /temp/
# build/
"""

class ConfigManager:
    """Manager for the single root configuration file"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the root configuration file. Defaults to ROOT_CONFIG_PATH.
        """
        logger.debug(f"Initializing ConfigManager with config_path: {config_path}")
        self.config_path = config_path or ROOT_CONFIG_PATH
        self.config = deepcopy(DEFAULT_CONFIG)

        # Load the root configuration file
        self._load_config()
        logger.debug(f"Config after loading: {self.config}")

        # Ensure essential structure exists in the loaded config
        if "projects" not in self.config or not isinstance(self.config.get("projects"), dict):
            logger.warning("'projects' key missing or not a dict in config. Resetting to empty dict.")
            self.config["projects"] = {}
        if "general" not in self.config:
            self.config["general"] = {}
        if "log_dir" not in self.config["general"]:
             self.config["general"]["log_dir"] = DEFAULT_LOG_DIR

        # Ensure log directory exists
        self._ensure_log_dir()

        # Keep a direct reference to the projects dictionary for convenience
        self.projects = self.config["projects"]

    def _ensure_log_dir(self) -> None:
        """Ensure the configured log directory exists"""
        try:
            log_dir = os.path.expanduser(self.config["general"]["log_dir"])
            self.config["general"]["log_dir"] = log_dir # Store expanded path
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create log directory '{self.config['general']['log_dir']}': {e}")

    def _load_config(self) -> None:
        """Load the root configuration from file if it exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    print(f"DEBUG: loaded_config = {loaded_config}")
                    logger.debug(f"Loaded raw config from {self.config_path}: {loaded_config}")
                    if loaded_config:
                        # Deep update the default config with loaded values
                        self._deep_update(self.config, loaded_config)
                        logger.info(f"Loaded configuration from {self.config_path}")
                        logger.debug(f"Updated config after loading: {self.config}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}. Using defaults.")
        else:
            logger.info(f"Configuration file not found at {self.config_path}. Creating with defaults.")
            # Create default config file if it doesn't exist
            self._save_config()

    def _save_config(self) -> None:
        """Save the current configuration to the root file"""
        try:
            # Ensure projects in self.config is up-to-date before saving
            self.config["projects"] = self.projects
            print(f"DEBUG: Saving config to {self.config_path} with projects =", self.config.get("projects"))
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")

    def add_project(self, project_path: str, project_name: Optional[str] = None) -> bool:
        """
        Add a project to the registry in the root config file.

        Args:
            project_path: Path to the project.
            project_name: Optional name for the project (defaults to directory name).

        Returns:
            bool: True if successful, False otherwise.
        """
        if not isinstance(self.projects, dict):
            logger.critical("Internal state error: self.projects is not a dictionary. Cannot add project.")
            return False

        try:
            abs_path = os.path.abspath(project_path)
            if not os.path.isdir(abs_path): # Check if it's a directory
                logger.error(f"Project path is not a valid directory: {abs_path}")
                return False

            # Use directory name as project name if not provided
            if not project_name:
                project_name = os.path.basename(abs_path)

            # Ensure unique name (append suffix if needed)
            base_name = project_name
            suffix = 1
            while project_name in self.projects and self.projects[project_name] != abs_path:
                 project_name = f"{base_name}_{suffix}"
                 suffix += 1

            # Check if path is already registered under a different name
            for name, path in self.projects.items():
                if path == abs_path and name != project_name:
                    logger.warning(f"Project path {abs_path} already registered as '{name}'. Not adding duplicate '{project_name}'.")
                    return False # Or maybe update the name? For now, prevent duplicates.

            # Add or update the project entry
            self.projects[project_name] = abs_path
            self._save_config()
            logger.info(f"Added/Updated project '{project_name}' with path '{abs_path}' to config.")
            return True
        except Exception as e:
            logger.error(f"Failed to add project '{project_name}': {e}")
            return False

    def remove_project(self, project_name: str) -> bool:
        """
        Remove a project from the registry in the root config file.

        Args:
            project_name: Name of the project to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not isinstance(self.projects, dict):
             logger.error("Internal state error: self.projects is not a dictionary. Cannot remove project.")
             return False

        if project_name in self.projects:
            project_path = self.projects[project_name]
            del self.projects[project_name]
            self._save_config()
            logger.info(f"Removed project '{project_name}' (path: {project_path}) from config.")
            return True
        else:
            logger.warning(f"Project '{project_name}' not found in config registry.")
            return False

    def get_project_path(self, project_name: str) -> Optional[str]:
        """
        Get the path for a project from the registry.

        Args:
            project_name: Name of the project.

        Returns:
            str: Path to the project, or None if not found.
        """
        if not isinstance(self.projects, dict):
             return None
        return self.projects.get(project_name)

    def get_all_projects(self) -> Dict[str, str]:
        """
        Get all registered projects from the config.

        Returns:
            Dict[str, str]: Dictionary of project names to paths. Returns empty dict if none.
        """
        projects = self.config.get("projects", {})
        return projects if isinstance(projects, dict) else {}

    def initialize_project(self, project_path: str, project_name: Optional[str] = None) -> bool:
        """
        Initializes the necessary structure within a project directory
        (.Augmentorium folder, subdirs, graph DB, .augmentoriumignore)
        and registers the project in the root config.

        Args:
            project_path: Path to the project directory.
            project_name: Optional name for the project.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            abs_path = os.path.abspath(project_path)

            # Create project directory if it doesn't exist
            os.makedirs(abs_path, exist_ok=True)

            # Create internal project directory (.Augmentorium)
            internal_dir = os.path.join(abs_path, PROJECT_INTERNAL_DIR_NAME)
            os.makedirs(internal_dir, exist_ok=True)

            # Create subdirectories within .Augmentorium
            os.makedirs(os.path.join(internal_dir, "chroma"), exist_ok=True)
            os.makedirs(os.path.join(internal_dir, "cache"), exist_ok=True)
            os.makedirs(os.path.join(internal_dir, "metadata"), exist_ok=True)

            # Initialize Graph DB within .Augmentorium
            try:
                graph_db_path = os.path.join(internal_dir, "code_graph.db")
                initialize_graph_db(graph_db_path)
                logger.info(f"Initialized graph database at {graph_db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize graph database for {abs_path}: {e}")
                # Continue initialization even if graph DB fails for now

            # Create default .augmentoriumignore file within .Augmentorium
            ignore_file_path = os.path.join(internal_dir, ".augmentoriumignore")
            if not os.path.exists(ignore_file_path):
                try:
                    with open(ignore_file_path, 'w') as f:
                        f.write(DEFAULT_IGNORE_CONTENT)
                    logger.info(f"Created default ignore file at {ignore_file_path}")
                except Exception as e:
                     logger.error(f"Failed to create ignore file at {ignore_file_path}: {e}")

            # Add project to the central registry (saves the config)
            # Determine the name to register
            final_project_name = project_name or os.path.basename(abs_path)
            if not self.add_project(abs_path, final_project_name):
                 # add_project logs the error
                 logger.error(f"Failed to register project '{final_project_name}' in the configuration file.")
                 return False # Registration failed

            logger.info(f"Successfully initialized project structure for '{final_project_name}' at '{abs_path}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize project structure at {project_path}: {e}")
            return False

    def get_db_path(self, project_path: str) -> str:
        """
        Get the path to the project's vector database directory.

        Args:
            project_path: Path to the project root.

        Returns:
            str: Path to the vector database directory.
        """
        return os.path.join(project_path, PROJECT_INTERNAL_DIR_NAME, "chroma")

    def get_cache_path(self, project_path: str) -> str:
        """
        Get the path to the project's cache directory.

        Args:
            project_path: Path to the project root.

        Returns:
            str: Path to the cache directory.
        """
        return os.path.join(project_path, PROJECT_INTERNAL_DIR_NAME, "cache")

    def get_metadata_path(self, project_path: str) -> str:
        """
        Get the path to the project's metadata directory.

        Args:
            project_path: Path to the project root.

        Returns:
            str: Path to the metadata directory.
        """
        return os.path.join(project_path, PROJECT_INTERNAL_DIR_NAME, "metadata")

    def get_graph_db_path(self, project_path: str) -> str:
        """
        Get the path to the project's graph database file.

        Args:
            project_path: Path to the project root.

        Returns:
            str: Path to the graph database file.
        """
        return os.path.join(project_path, PROJECT_INTERNAL_DIR_NAME, "code_graph.db")

    def get_project_ignore_file_path(self, project_path: str) -> str:
        """
        Get the path to the project's specific ignore file.

        Args:
            project_path: Path to the project root.

        Returns:
            str: Path to the .augmentoriumignore file.
        """
        return os.path.join(project_path, PROJECT_INTERNAL_DIR_NAME, ".augmentoriumignore")

    def reload(self):
        """
        Reload the root configuration from disk.
        """
        logger.info(f"Reloading configuration from {self.config_path}")
        # Reset to defaults before loading to ensure clean state
        self.config = deepcopy(DEFAULT_CONFIG)
        self._load_config()
        # Re-link self.projects
        if "projects" not in self.config or not isinstance(self.config.get("projects"), dict):
            self.config["projects"] = {}
        self.projects = self.config["projects"]


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
