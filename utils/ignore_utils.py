import os
from typing import List
import pathspec
from config.manager import ConfigManager
from utils.path_utils import get_relative_path

def load_ignore_patterns(config_manager: ConfigManager, project_path: str) -> List[str]:
    """
    Load ignore patterns from config.yaml and the project-specific ignore file.
    Combines and deduplicates patterns.
    """
    # Load base patterns from config.yaml
    base_patterns = config_manager.config.get("indexer", {}).get("ignore_patterns", [])
    # Load project-specific patterns
    project_ignore_file = config_manager.get_project_ignore_file_path(project_path)
    project_patterns = []
    if os.path.exists(project_ignore_file):
        with open(project_ignore_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    project_patterns.append(line)
    # Combine and deduplicate
    return list(set(base_patterns + project_patterns))

def get_ignore_spec(config_manager: ConfigManager, project_path: str) -> pathspec.PathSpec:
    """
    Returns a compiled PathSpec object using the combined ignore patterns.
    """
    patterns = load_ignore_patterns(config_manager, project_path)
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

def should_ignore(path: str, project_path: str, ignore_spec: pathspec.PathSpec) -> bool:
    """
    Returns True if the given path should be ignored, using the ignore_spec and relative path logic.
    """
    rel_path = get_relative_path(path, project_path)
    return ignore_spec.match_file(rel_path)