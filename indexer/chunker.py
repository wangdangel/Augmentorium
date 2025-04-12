"""
[MODULARIZED] This file has been modularized. The Chunker class remains here temporarily and this file is pending removal after migration is validated.

Main chunker for code files in Augmentorium.
"""

import os
import logging
from typing import Dict, List, Optional, Any

from indexer.chunking_strategy_factory import ChunkingStrategyFactory
from indexer.code_chunk import CodeChunk

logger = logging.getLogger(__name__)

class Chunker:
    """Main chunker for code files"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize chunker

        Args:
            config: Chunking configuration
        """
        self.config = config or {}
        self.factory = ChunkingStrategyFactory(self.config)

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a file

        Args:
            file_path: Path to the file

        Returns:
            List[CodeChunk]: List of code chunks
        """
        try:
            # Get the appropriate strategy
            strategy = self.factory.get_strategy(file_path)

            # Chunk the file
            chunks = strategy.chunk_file(file_path)

            # Enrich chunks with additional metadata
            self._enrich_chunks(chunks, file_path)

            return chunks
        except Exception as e:
            logger.error(f"Failed to chunk file {file_path}: {e}")
            return []

    def _enrich_chunks(self, chunks: List[CodeChunk], file_path: str) -> None:
        """
        Enrich chunks with additional metadata

        Args:
            chunks: List of chunks
            file_path: Path to the file
        """
        # Add file information
        file_stat = os.stat(file_path)
        file_info = {
            "file_name": os.path.basename(file_path),
            "file_size": file_stat.st_size,
            "last_modified": file_stat.st_mtime,
        }

        # Add relationship information
        for i, chunk in enumerate(chunks):
            # Add file info
            chunk.metadata.update(file_info)

            # Add chunk index
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
