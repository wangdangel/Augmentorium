"""
Base class for chunking strategies in Augmentorium.
"""

from typing import List
from indexer.code_chunk import CodeChunk

class ChunkingStrategy:
    """Base class for chunking strategies"""

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a file

        Args:
            file_path: Path to the file

        Returns:
            List[CodeChunk]: List of code chunks
        """
        raise NotImplementedError("Subclasses must implement this method")