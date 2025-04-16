"""
Augmentorium: A code-aware RAG system for LLM access to codebases
"""

__version__ = "0.1.0"
__author__ = "Augmentorium Team"
__license__ = "MIT"
__copyright__ = "Copyright 2025, Augmentorium Team"

# Import key components for easier access
from augmentorium.config.manager import ConfigManager
from augmentorium.indexer import start_indexer
from augmentorium.server import start_server
