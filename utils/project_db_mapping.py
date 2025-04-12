"""
project_db_mapping.py

Provides utilities for building and managing mappings from project names and paths
to their associated database file locations.

API:
- build_project_db_mapping(config_manager): Returns a dictionary mapping both project names and absolute paths
  to a dictionary containing absolute paths to code_graph.db and chroma/chroma.sqlite3 for each project.
- get_db_paths_for_project(mapping, project_name_or_path): Returns the database paths dictionary for a given
  project (by name or path), or None if not found.

This module is designed to be well-documented and easy to extend.
"""

import os

def build_project_db_mapping(config_manager):
    """
    Constructs a mapping from project names and absolute paths to their database file locations.

    Args:
        config_manager: An object that provides access to project configuration.
            Must implement get_projects(), returning a list of dicts with at least 'name' and 'path' keys.

    Returns:
        dict: A mapping where each key is either a project name or absolute path,
              and each value is a dict with:
                  - 'code_graph_db': absolute path to code_graph.db
                  - 'chroma_db': absolute path to chroma/chroma.sqlite3
    """
    mapping = {}
    projects = [{"name": name, "path": path} for name, path in config_manager.get_all_projects().items()]
    for project in projects:
        name = project["name"]
        path = os.path.abspath(project["path"])
        code_graph_db = os.path.join(path, "code_graph.db")
        chroma_db = os.path.join(path, "chroma", "chroma.sqlite3")
        db_paths = {
            "code_graph_db": code_graph_db,
            "chroma_db": chroma_db
        }
        mapping[name] = db_paths
        mapping[path] = db_paths
    return mapping

def get_db_paths_for_project(mapping, project_name_or_path):
    """
    Retrieves the database paths for a given project by name or absolute path.

    Args:
        mapping (dict): The mapping produced by build_project_db_mapping.
        project_name_or_path (str): The project name or absolute path.

    Returns:
        dict or None: The database paths dictionary for the project, or None if not found.
    """
    if project_name_or_path is None:
        return None
    if project_name_or_path in mapping:
        return mapping[project_name_or_path]
    abs_path = os.path.abspath(project_name_or_path)
    return mapping.get(abs_path)