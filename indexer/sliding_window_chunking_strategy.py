"""
Chunking strategy based on sliding window for Augmentorium.
"""

import logging
from typing import List

from indexer.chunking_strategy_base import ChunkingStrategy
from indexer.code_chunk import CodeChunk
from utils.path_utils import get_file_extension

logger = logging.getLogger(__name__)

class SlidingWindowChunkingStrategy(ChunkingStrategy):
    """Chunking strategy based on sliding window"""

    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        min_chunk_size: int = 64
    ):
        """
        Initialize sliding window chunking strategy

        Args:
            chunk_size: Maximum size of a chunk
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size of a chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a file using sliding window

        Args:
            file_path: Path to the file

        Returns:
            List[CodeChunk]: List of code chunks
        """
        try:
            logger.debug(f"[SlidingWindowChunking] Opening file: {file_path}")
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            logger.debug(f"[SlidingWindowChunking] Finished reading file: {file_path} ({len(content)} bytes)")

            # Get language from file extension
            ext = get_file_extension(file_path)
            language = ext.lstrip(".") if ext else None

            # Split content into lines for line tracking
            lines = content.split("\n")

            # Create chunks
            chunks = []
            start_idx = 0

            while start_idx < len(content):
                # Calculate end index
                end_idx = min(start_idx + self.chunk_size, len(content))

                # Adjust end index to a line boundary
                while end_idx < len(content) and content[end_idx] != "\n":
                    end_idx += 1

                # Check if we're at the end of the content
                if end_idx >= len(content):
                    end_idx = len(content)
                else:
                    # Include the newline
                    end_idx += 1

                # Get the chunk text
                chunk_text = content[start_idx:end_idx]

                # Skip if chunk is too small and not the last chunk
                if len(chunk_text) < self.min_chunk_size and end_idx < len(content):
                    start_idx = end_idx
                    continue

                # Calculate start and end lines
                start_line = content[:start_idx].count("\n")
                end_line = start_line + chunk_text.count("\n")

                # Create metadata
                metadata = {
                    "chunk_index": len(chunks),
                    "total_lines": len(lines)
                }

                # Create the chunk
                chunk = CodeChunk(
                    text=chunk_text,
                    chunk_type="sliding_window",
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    language=language,
                    metadata=metadata
                )

                # Add the chunk
                chunks.append(chunk)

                # Move start index for next chunk
                next_start_idx = end_idx - self.chunk_overlap
                if next_start_idx <= start_idx:
                    next_start_idx = end_idx
                if next_start_idx <= start_idx:
                    # Prevent infinite loop
                    break
                start_idx = next_start_idx

            logger.debug(f"[SlidingWindowChunking] Finished chunking file: {file_path} into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Failed to chunk file {file_path}: {e}")
            return []