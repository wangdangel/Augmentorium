"""
Default configuration values for Augmentorium
"""

import os
from pathlib import Path

# Base directories
HOME_DIR = str(Path.home())
# Note: GLOBAL_CONFIG_DIR removed. Log directory should be defined in root config.yaml.
# We'll keep DEFAULT_LOG_DIR temporarily as a fallback if not specified in config.
# DEFAULT_LOG_DIR = os.path.join(HOME_DIR, ".augmentorium", "logs")  # Deprecated: log_dir now set relative to project root
# Project root directory (parent of this config directory)
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_LOG_DIR = str(PROJECT_ROOT / "logs")  # Default: logs directory in project root

# Project-specific directory name (used within project folders)
PROJECT_INTERNAL_DIR_NAME = ".Augmentorium"

# Default configuration structure (for the single root config.yaml)
DEFAULT_CONFIG = {
    "general": {
        "log_dir": "logs", # Default log location relative to project root
        "log_level": "INFO",
    },
    # Project registry - now part of the main config
    "projects": {},
    # Removed legacy 'active_project' entry; all projects are always available
    "indexer": {
        "polling_interval": 1.0,  # seconds
        "max_workers": 4,
        "hash_algorithm": "md5",
    },
    "server": {
        "host": "localhost",
        "port": 6655,
        "cache_size": 100,
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "embedding_model": "bge-m3:latest",
        "embedding_batch_size": 10,
    }, # Added missing closing brace
    # Removed duplicate indexer, server, ollama sections below
    "chunking": { # Default chunking settings
        "max_chunk_size": 1024,
        "chunk_overlap": 128,
        "min_chunk_size": 64,
    },
    "languages": {
        "python": {
            "extensions": [".py"],
            "chunking_strategy": "ast",
        },
        "javascript": {
            "extensions": [".js", ".jsx", ".ts", ".tsx"],
            "chunking_strategy": "ast",
        },
        "html": {
            "extensions": [".html", ".htm"],
            "chunking_strategy": "sliding_window",
        },
        "css": {
            "extensions": [".css", ".scss", ".sass", ".less"],
            "chunking_strategy": "sliding_window",
        },
        "json": {
            "extensions": [".json"],
            "chunking_strategy": "json_object",
        },
        "yaml": {
            "extensions": [".yaml", ".yml"],
            "chunking_strategy": "yaml_document",
        },
        "markdown": {
            "extensions": [".md", ".markdown"],
            "chunking_strategy": "markdown_section",
        },
        "text": {
            "extensions": [".txt"],
            "chunking_strategy": "sliding_window",
        },
    },
}
