"""
Default configuration values for Augmentorium
"""

import os
from pathlib import Path

# Base directories
HOME_DIR = str(Path.home())
GLOBAL_CONFIG_DIR = os.path.join(HOME_DIR, ".augmentorium")
DEFAULT_LOG_DIR = os.path.join(GLOBAL_CONFIG_DIR, "logs")

# Project-specific directories
PROJECT_CONFIG_DIR = ".augmentorium"
PROJECT_DB_DIR = "chroma"
PROJECT_CACHE_DIR = "cache"
PROJECT_METADATA_DIR = "metadata"

# Default global configuration
DEFAULT_GLOBAL_CONFIG = {
    "general": {
        "log_dir": DEFAULT_LOG_DIR,
        "log_level": "INFO",
    },
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
        "embedding_model": "codellama",
        "embedding_batch_size": 10,
    },
}

# Default project configuration
DEFAULT_PROJECT_CONFIG = {
    "project": {
        "name": "default",
        "exclude_patterns": [
            "**/.git/**",
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/.venv/**",
            "**/venv/**",
            "**/.env/**",
            "**/.idea/**",
            "**/.vscode/**",
            "**/.DS_Store",
            "**/dist/**",
            "**/build/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
        ],
    },
    "chunking": {
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
