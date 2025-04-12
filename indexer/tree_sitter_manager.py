"""
Manager for Tree-sitter languages and parsers.

This module was extracted from parser.py as part of modularization.
"""

import os
import logging
from typing import Dict, Any, Optional
from tree_sitter_language_pack import get_language, get_parser

from indexer.language_map import EXTENSION_TO_LANGUAGE

logger = logging.getLogger(__name__)

class TreeSitterManager:
    """Manager for Tree-sitter languages and parsers"""

    def parse_file(self, file_path: str) -> Optional['Tree']:
        """
        Parse a file and return the Tree-sitter parse tree.

        Args:
            file_path: Path to the file

        Returns:
            Tree object if successful, None otherwise
        """
        try:
            language = self.detect_language(file_path)
            if not language:
                logger.warning(f"Could not detect language for file: {file_path}")
                return None
            if not self.load_language(language):
                logger.warning(f"Language '{language}' not available, cannot parse file: {file_path}")
                return None
            parser = self.parsers.get(language)
            if not parser:
                logger.warning(f"No parser found for language: {language}")
                return None
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            tree = parser.parse(bytes(content, "utf8"))
            return tree
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return None

    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect programming language based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language string compatible with Tree-sitter, or None if unknown
        """
        ext = os.path.splitext(file_path)[1].lower()
        return EXTENSION_TO_LANGUAGE.get(ext)

    def __init__(self):
        """
        Initialize Tree-sitter manager.
        """
        self.languages: Dict[str, Any] = {}
        self.parsers: Dict[str, Any] = {}
        logger.info("Initialized Tree-sitter manager using language pack with plain text fallback.")

    def load_language(self, language_name: str) -> bool:
        """
        Load a Tree-sitter language using the language pack.
        Falls back to plain text if not available.
        """
        if language_name in self.languages:
            return True
        try:
            parser = get_parser(language_name)
            language = get_language(language_name)
            self.parsers[language_name] = parser
            self.languages[language_name] = language
            logger.info(f"Loaded language from language pack: {language_name}")
            return True
        except Exception as e:
            logger.warning(f"Language '{language_name}' not found in language pack, falling back to plain text: {e}")
            return False