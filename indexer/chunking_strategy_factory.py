"""
Factory for creating chunking strategies in Augmentorium.
"""

from typing import Dict, Any, Optional

from indexer.ast_chunking_strategy import ASTChunkingStrategy
from indexer.sliding_window_chunking_strategy import SlidingWindowChunkingStrategy
from indexer.json_object_chunking_strategy import JsonObjectChunkingStrategy
from indexer.yaml_document_chunking_strategy import YamlDocumentChunkingStrategy
from indexer.markdown_section_chunking_strategy import MarkdownSectionChunkingStrategy
from indexer.code_parser import CodeParser
from utils.path_utils import get_file_extension

class ChunkingStrategyFactory:
    """Factory for creating chunking strategies"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize chunking strategy factory

        Args:
            config: Chunking configuration
        """
        self.config = config or {}
        self.code_parser = CodeParser()

        # Create default strategies
        self.ast_strategy = ASTChunkingStrategy(self.code_parser)
        self.sliding_window_strategy = SlidingWindowChunkingStrategy(
            chunk_size=self.config.get("max_chunk_size", 1024),
            chunk_overlap=self.config.get("chunk_overlap", 128),
            min_chunk_size=self.config.get("min_chunk_size", 64)
        )
        self.json_strategy = JsonObjectChunkingStrategy()
        self.yaml_strategy = YamlDocumentChunkingStrategy()
        self.markdown_strategy = MarkdownSectionChunkingStrategy()

    def get_strategy(self, file_path: str):
        """
        Get the appropriate chunking strategy for a file

        Args:
            file_path: Path to the file

        Returns:
            ChunkingStrategy: Chunking strategy
        """
        # Get file extension
        ext = get_file_extension(file_path)

        # Get language configuration
        languages_config = self.config.get("languages", {})

        # Find the language by extension in config
        for lang, lang_config in languages_config.items():
            extensions = lang_config.get("extensions", [])
            if ext in extensions:
                # Get chunking strategy
                strategy_name = lang_config.get("chunking_strategy", "sliding_window")
                return self._create_strategy(strategy_name)

        # Use dynamic extension-to-language mapping for AST chunking
        from indexer.language_map import EXTENSION_TO_LANGUAGE
        if ext in EXTENSION_TO_LANGUAGE:
            return self.ast_strategy
        elif ext in [".json"]:
            return self.json_strategy
        elif ext in [".yaml", ".yml"]:
            return self.yaml_strategy
        elif ext in [".md", ".markdown"]:
            return self.markdown_strategy
        else:
            return self.sliding_window_strategy

    def _create_strategy(self, strategy_name: str):
        """
        Create a chunking strategy by name

        Args:
            strategy_name: Name of the strategy

        Returns:
            ChunkingStrategy: Chunking strategy
        """
        if strategy_name == "ast":
            return self.ast_strategy
        elif strategy_name == "json_object":
            return self.json_strategy
        elif strategy_name == "yaml_document":
            return self.yaml_strategy
        elif strategy_name == "markdown_section":
            return self.markdown_strategy
        else:
            return self.sliding_window_strategy