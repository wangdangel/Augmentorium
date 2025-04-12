"""
Chunking strategy for YAML files in Augmentorium.
"""

import logging
from typing import List

from indexer.chunking_strategy_base import ChunkingStrategy
from indexer.code_chunk import CodeChunk

logger = logging.getLogger(__name__)

class YamlDocumentChunkingStrategy(ChunkingStrategy):
    """Chunking strategy for YAML files"""

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a YAML file

        Args:
            file_path: Path to the file

        Returns:
            List[CodeChunk]: List of code chunks
        """
        try:
            # For YAML, we'll use a simple document-based chunking
            # since proper YAML parsing is complex

            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Split content into lines
            lines = content.split("\n")

            # Find document separators
            doc_indexes = [-1]  # Start with -1 for the first document

            for i, line in enumerate(lines):
                if line.strip() == "---":
                    doc_indexes.append(i)

            doc_indexes.append(len(lines))  # Add the end of the file

            # Create chunks for each document
            chunks = []

            for i in range(len(doc_indexes) - 1):
                start_idx = doc_indexes[i] + 1
                end_idx = doc_indexes[i + 1]

                # Skip empty documents
                if end_idx - start_idx <= 1:
                    continue

                # Get document text
                doc_text = "\n".join(lines[start_idx:end_idx])

                # Create metadata
                metadata = {
                    "document_index": i,
                    "total_documents": len(doc_indexes) - 1
                }

                # Create the chunk
                chunk = CodeChunk(
                    text=doc_text,
                    chunk_type="yaml_document",
                    file_path=file_path,
                    start_line=start_idx,
                    end_line=end_idx - 1,
                    name=f"document_{i}",
                    language="yaml",
                    metadata=metadata
                )

                # Add the chunk
                chunks.append(chunk)

            return chunks
        except Exception as e:
            logger.error(f"Failed to chunk YAML file {file_path}: {e}")
            return []