"""
Chunking strategy for Markdown files in Augmentorium.
"""

import logging
from typing import List

from indexer.chunking_strategy_base import ChunkingStrategy
from indexer.code_chunk import CodeChunk

logger = logging.getLogger(__name__)

class MarkdownSectionChunkingStrategy(ChunkingStrategy):
    """Chunking strategy for Markdown files"""

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a Markdown file

        Args:
            file_path: Path to the file

        Returns:
            List[CodeChunk]: List of code chunks
        """
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Split content into lines
            lines = content.split("\n")

            # Find headers
            header_indexes = []
            header_levels = []
            header_texts = []

            for i, line in enumerate(lines):
                if line.startswith("#"):
                    # Count header level (number of # symbols)
                    level = 0
                    for char in line:
                        if char == "#":
                            level += 1
                        else:
                            break

                    # Skip if not a valid header (needs space after #)
                    if len(line) <= level or line[level] != " ":
                        continue

                    # Get header text
                    header_text = line[level + 1:].strip()

                    header_indexes.append(i)
                    header_levels.append(level)
                    header_texts.append(header_text)

            # Add the end of the file
            header_indexes.append(len(lines))

            # Create chunks for each section
            chunks = []

            for i in range(len(header_indexes) - 1):
                start_idx = header_indexes[i]
                end_idx = header_indexes[i + 1]

                # Get section text
                section_text = "\n".join(lines[start_idx:end_idx])

                # Create metadata
                metadata = {
                    "header_level": header_levels[i] if i < len(header_levels) else 0,
                    "header_text": header_texts[i] if i < len(header_texts) else "",
                    "section_index": i,
                    "total_sections": len(header_indexes) - 1
                }

                # Create the chunk
                chunk = CodeChunk(
                    text=section_text,
                    chunk_type="markdown_section",
                    file_path=file_path,
                    start_line=start_idx,
                    end_line=end_idx - 1,
                    name=metadata["header_text"],
                    language="markdown",
                    metadata=metadata
                )

                # Add the chunk
                chunks.append(chunk)

            # If there are no headers, create a single chunk for the whole file
            if len(chunks) == 0:
                chunk = CodeChunk(
                    text=content,
                    chunk_type="markdown_document",
                    file_path=file_path,
                    start_line=0,
                    end_line=len(lines) - 1,
                    language="markdown",
                    metadata={"total_lines": len(lines)}
                )
                chunks.append(chunk)

            return chunks
        except Exception as e:
            logger.error(f"Failed to chunk Markdown file {file_path}: {e}")
            return []