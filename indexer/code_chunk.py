"""
Representation of a code chunk for embedding in Augmentorium.
"""

import os
from typing import Dict, Optional, Any

class CodeChunk:
    """Representation of a code chunk for embedding"""

    def __init__(
        self,
        text: str,
        chunk_type: str,
        file_path: str,
        start_line: int,
        end_line: int,
        name: Optional[str] = None,
        language: Optional[str] = None,
        parent_chunk: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a code chunk

        Args:
            text: Text content of the chunk
            chunk_type: Type of chunk (function, class, etc.)
            file_path: Path to the file
            start_line: Start line number
            end_line: End line number
            name: Name of the chunk
            language: Language of the code
            parent_chunk: ID of the parent chunk
            metadata: Additional metadata
        """
        self.text = text
        self.chunk_type = chunk_type
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.name = name
        self.language = language
        self.parent_chunk = parent_chunk
        self.metadata = metadata or {}

        # Generate a unique ID for the chunk
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """
        Generate a unique ID for the chunk

        Returns:
            str: Unique ID
        """
        # Use file path, chunk type, and line range to create a unique ID
        base_path = os.path.basename(self.file_path)
        name_part = f"_{self.name}" if self.name else ""
        return f"{base_path}{name_part}_{self.chunk_type}_{self.start_line}_{self.end_line}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "id": self.id,
            "text": self.text,
            "chunk_type": self.chunk_type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "name": self.name,
            "language": self.language,
            "parent_chunk": self.parent_chunk,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeChunk':
        """
        Create a chunk from dictionary

        Args:
            data: Dictionary representation

        Returns:
            CodeChunk: New code chunk
        """
        chunk = cls(
            text=data["text"],
            chunk_type=data["chunk_type"],
            file_path=data["file_path"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            name=data.get("name"),
            language=data.get("language"),
            parent_chunk=data.get("parent_chunk"),
            metadata=data.get("metadata", {})
        )

        # Override the generated ID with the stored one
        if "id" in data:
            chunk.id = data["id"]

        return chunk