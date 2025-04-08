"""
Path utilities for cross-platform compatibility
"""

import os
import sys
import re
import fnmatch
from pathlib import Path
from typing import List, Set, Optional, Tuple

def normalize_path(path: str) -> str:
    """
    Normalize a path for cross-platform compatibility
    
    Args:
        path: Path to normalize
        
    Returns:
        str: Normalized path
    """
    return os.path.normpath(os.path.abspath(path))

def is_windows() -> bool:
    """
    Check if the current platform is Windows
    
    Returns:
        bool: True if Windows, False otherwise
    """
    return sys.platform.startswith('win')

def is_macos() -> bool:
    """
    Check if the current platform is macOS
    
    Returns:
        bool: True if macOS, False otherwise
    """
    return sys.platform.startswith('darwin')

def is_linux() -> bool:
    """
    Check if the current platform is Linux
    
    Returns:
        bool: True if Linux, False otherwise
    """
    return sys.platform.startswith('linux')

def get_relative_path(path: str, base_path: str) -> str:
    """
    Get the relative path from a base path
    
    Args:
        path: Path to convert to relative
        base_path: Base path to make the path relative to
        
    Returns:
        str: Relative path
    """
    try:
        return os.path.relpath(path, base_path)
    except ValueError:
        # Handle Windows paths on different drives
        if is_windows():
            # Just return the path if it's on a different drive
            return path
        raise

def make_path_platform_agnostic(path: str) -> str:
    """
    Make a path platform agnostic by replacing backslashes with forward slashes
    
    Args:
        path: Path to convert
        
    Returns:
        str: Platform agnostic path
    """
    return path.replace('\\', '/')

def get_path_hash_key(path: str, base_path: Optional[str] = None) -> str:
    """
    Get a consistent hash key for a path, optionally relative to a base path
    
    Args:
        path: Path to hash
        base_path: Optional base path for relative paths
        
    Returns:
        str: Consistent hash key
    """
    if base_path:
        path = get_relative_path(path, base_path)
    return make_path_platform_agnostic(path)

def matches_any_pattern(path: str, patterns: List[str]) -> bool:
    """
    Check if a path matches any of the given glob patterns
    
    Args:
        path: Path to check
        patterns: List of glob patterns
        
    Returns:
        bool: True if path matches any pattern, False otherwise
    """
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def find_files(
    directory: str, 
    include_extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_depth: Optional[int] = None
) -> List[str]:
    """
    Find files in a directory with optional filtering
    
    Args:
        directory: Directory to search
        include_extensions: Optional list of file extensions to include
        exclude_patterns: Optional list of glob patterns to exclude
        max_depth: Optional maximum directory depth to search
        
    Returns:
        List[str]: List of matching file paths
    """
    result = []
    directory = normalize_path(directory)
    
    for root, dirs, files in os.walk(directory):
        # Check depth
        if max_depth is not None:
            depth = root[len(directory):].count(os.sep)
            if depth >= max_depth:
                dirs.clear()  # Don't go deeper
        
        # Apply exclude patterns to directories
        if exclude_patterns:
            dirs_to_remove = []
            for d in dirs:
                dir_path = os.path.join(root, d)
                rel_path = os.path.relpath(dir_path, directory)
                if matches_any_pattern(rel_path, exclude_patterns):
                    dirs_to_remove.append(d)
            
            for d in dirs_to_remove:
                dirs.remove(d)
        
        # Process files
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, directory)
            
            # Skip excluded files
            if exclude_patterns and matches_any_pattern(rel_path, exclude_patterns):
                continue
            
            # Check file extensions
            if include_extensions:
                _, ext = os.path.splitext(file)
                if ext.lower() not in include_extensions:
                    continue
            
            result.append(file_path)
    
    return result

def get_file_extension(path: str) -> str:
    """
    Get the file extension in lowercase
    
    Args:
        path: Path to get extension from
        
    Returns:
        str: Lowercase file extension including the dot
    """
    _, ext = os.path.splitext(path)
    return ext.lower()

def get_file_name(path: str) -> str:
    """
    Get the file name without path
    
    Args:
        path: Path to get file name from
        
    Returns:
        str: File name without path
    """
    return os.path.basename(path)

def get_project_root(file_path: str) -> Optional[str]:
    """
    Try to find the project root by looking for common project markers
    
    Args:
        file_path: Path of a file in the project
        
    Returns:
        Optional[str]: Project root path, or None if not found
    """
    path = Path(file_path).resolve()
    
    # If path is a file, start from its parent directory
    if path.is_file():
        path = path.parent
    
    # Common project markers
    markers = [
        '.git',
        '.svn',
        '.hg',
        'pyproject.toml',
        'setup.py',
        'package.json',
        'Cargo.toml',
        'Gemfile',
        'pom.xml',
        'build.gradle',
        '.augmentorium'
    ]
    
    # Go up the directory tree
    while True:
        for marker in markers:
            if (path / marker).exists():
                return str(path)
        
        # Stop if we've reached the root
        if path.parent == path:
            break
            
        path = path.parent
    
    return None

def split_path_components(path: str) -> List[str]:
    """
    Split a path into its components
    
    Args:
        path: Path to split
        
    Returns:
        List[str]: List of path components
    """
    path = normalize_path(path)
    components = []
    
    while True:
        path, folder = os.path.split(path)
        
        if folder:
            components.append(folder)
        else:
            if path:
                components.append(path)
            break
    
    components.reverse()
    return components
