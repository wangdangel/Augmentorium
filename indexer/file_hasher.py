"""
FileHasher: Utility for tracking file changes via hashing.
Moved from indexer/watcher.py as part of modular refactor.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Optional
from utils.path_utils import get_path_hash_key

logger = logging.getLogger(__name__)

class FileHasher:
    """Utility for tracking file changes via hashing"""
    
    def __init__(self, algorithm: str = "md5"):
        """
        Initialize the file hasher
        
        Args:
            algorithm: Hash algorithm to use
        """
        self.algorithm = algorithm
        self.hash_cache: Dict[str, str] = {}
    
    def compute_hash(self, file_path: str) -> Optional[str]:
        """
        Compute the hash of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[str]: Hash of the file contents, or None if error
        """
        try:
            hasher = hashlib.new(self.algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute hash for {file_path}: {e}")
            return None
    
    def has_changed(self, file_path: str) -> bool:
        """
        Check if a file has changed since the last check
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if the file has changed or is new, False otherwise
        """
        # Normalize path for consistent key
        key = get_path_hash_key(file_path)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            if key in self.hash_cache:
                del self.hash_cache[key]
            return False
        
        # Compute new hash
        new_hash = self.compute_hash(file_path)
        if new_hash is None:
            return False
        
        # Check if hash has changed
        old_hash = self.hash_cache.get(key)
        has_changed = old_hash != new_hash
        
        # Update hash cache
        self.hash_cache[key] = new_hash
        
        return has_changed
    
    def update_hash(self, file_path: str) -> None:
        """
        Update the hash cache for a file
        
        Args:
            file_path: Path to the file
        """
        key = get_path_hash_key(file_path)
        new_hash = self.compute_hash(file_path)
        if new_hash:
            self.hash_cache[key] = new_hash
    
    def remove_hash(self, file_path: str) -> None:
        """
        Remove a file from the hash cache
        
        Args:
            file_path: Path to the file
        """
        key = get_path_hash_key(file_path)
        if key in self.hash_cache:
            del self.hash_cache[key]
    
    def load_cache(self, cache_file: str) -> bool:
        """
        Load hash cache from file
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(cache_file):
                return False
            
            with open(cache_file, "r") as f:
                self.hash_cache = json.loads(f.read())
            
            return True
        except Exception as e:
            logger.error(f"Failed to load hash cache from {cache_file}: {e}")
            return False
    
    def save_cache(self, cache_file: str) -> bool:
        """
        Save hash cache to file
        
        Args:
            cache_file: Path to the cache file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            with open(cache_file, "w") as f:
                f.write(json.dumps(self.hash_cache))
            
            return True
        except Exception as e:
            logger.error(f"Failed to save hash cache to {cache_file}: {e}")
            return False