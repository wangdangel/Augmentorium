"""
Chunking strategy based on AST for Augmentorium.
"""

import logging
from typing import List, Optional

from indexer.chunking_strategy_base import ChunkingStrategy
from indexer.code_chunk import CodeChunk
from indexer.code_structure import CodeStructure
from indexer.code_parser import CodeParser

logger = logging.getLogger(__name__)

class ASTChunkingStrategy(ChunkingStrategy):
    """Chunking strategy based on AST"""

    def __init__(self, code_parser: Optional[CodeParser] = None):
        """
        Initialize AST chunking strategy

        Args:
            code_parser: Code parser
        """
        self.code_parser = code_parser or CodeParser()

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a file using AST

        Args:
            file_path: Path to the file

        Returns:
            List[CodeChunk]: List of code chunks
        """
        try:
            # Parse the file
            code_structure = self.code_parser.parse_file(file_path)
            if not code_structure:
                logger.warning(f"Failed to parse file for chunking: {file_path}")
                return []

            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Create chunks from code structure
            chunks = []
            self._process_structure(code_structure, content, chunks)

            return chunks
        except Exception as e:
            logger.error(f"Failed to chunk file {file_path}: {e}")
            return []

    def _process_structure(
        self,
        structure: CodeStructure,
        content: str,
        chunks: List[CodeChunk],
        parent_id: Optional[str] = None
    ) -> None:
        """
        Process code structure and create chunks

        Args:
            structure: Code structure
            content: File content
            chunks: List to add chunks to
            parent_id: ID of the parent chunk
        """
        # Extract lines for this structure
        start_line, end_line = structure.get_line_range()

        # Get the text content for this structure
        lines = content.split("\n")
        text = "\n".join(lines[start_line:end_line + 1])

        # Create metadata
        metadata = {
            "imports": structure.imports,
            "references": list(structure.references),
            "docstring": structure.docstring,
            "full_name": structure.get_full_name(),
            "path": structure.get_path(),
        }

        # Add additional metadata from structure
        metadata.update(structure.metadata)

        # Create the chunk
        chunk = CodeChunk(
            text=text,
            chunk_type=structure.node_type,
            file_path=structure.file_path,
            start_line=start_line,
            end_line=end_line,
            name=structure.name,
            language=structure.language,
            parent_chunk=parent_id,
            metadata=metadata
        )

        # Add the chunk
        chunks.append(chunk)

        # Process children
        for child in structure.children:
            self._process_structure(child, content, chunks, chunk.id)