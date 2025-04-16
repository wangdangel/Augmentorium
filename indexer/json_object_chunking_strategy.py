"""
Chunking strategy for JSON files in Augmentorium.
"""

import json
import json5
import logging
from typing import List, Optional, Any

from indexer.chunking_strategy_base import ChunkingStrategy
from indexer.code_chunk import CodeChunk

logger = logging.getLogger(__name__)

class JsonObjectChunkingStrategy(ChunkingStrategy):
    """Chunking strategy for JSON files"""

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a JSON file

        Args:
            file_path: Path to the file

        Returns:
            List[CodeChunk]: List of code chunks
        """
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Parse JSON (lenient, supports comments/trailing commas)
            data = json5.loads(content)

            # Create chunks
            chunks = []
            self._process_json_object(data, file_path, content.split("\n"), chunks)

            return chunks
        except Exception as e:
            logger.error(f"Failed to chunk JSON file {file_path}: {e}")
            return []

    def _process_json_object(
        self,
        data: Any,
        file_path: str,
        lines: List[str],
        chunks: List[CodeChunk],
        path: str = "$",
        parent_id: Optional[str] = None
    ) -> None:
        """
        Process a JSON object and create chunks

        Args:
            data: JSON data
            file_path: Path to the file
            lines: File content lines
            chunks: List to add chunks to
            path: JSON path
            parent_id: ID of the parent chunk
        """
        if isinstance(data, dict):
            # Process dictionary
            for key, value in data.items():
                if isinstance(value, (dict, list)) and len(json.dumps(value)) > 50:
                    # Create a chunk for complex value
                    value_text = json.dumps(value, indent=2)
                    value_path = f"{path}.{key}"

                    # Create metadata
                    metadata = {
                        "json_path": value_path,
                        "parent_path": path
                    }

                    # Create the chunk
                    chunk = CodeChunk(
                        text=value_text,
                        chunk_type="json_object",
                        file_path=file_path,
                        start_line=0,  # Placeholder
                        end_line=0,    # Placeholder
                        name=key,
                        language="json",
                        parent_chunk=parent_id,
                        metadata=metadata
                    )

                    # Add the chunk
                    chunks.append(chunk)

                    # Process the value recursively
                    self._process_json_object(value, file_path, lines, chunks, value_path, chunk.id)

        elif isinstance(data, list):
            # Process list
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)) and len(json.dumps(item)) > 50:
                    # Create a chunk for complex item
                    item_text = json.dumps(item, indent=2)
                    item_path = f"{path}[{i}]"

                    # Create metadata
                    metadata = {
                        "json_path": item_path,
                        "parent_path": path,
                        "array_index": i
                    }

                    # Create the chunk
                    chunk = CodeChunk(
                        text=item_text,
                        chunk_type="json_array_item",
                        file_path=file_path,
                        start_line=0,  # Placeholder
                        end_line=0,    # Placeholder
                        name=f"item_{i}",
                        language="json",
                        parent_chunk=parent_id,
                        metadata=metadata
                    )

                    # Add the chunk
                    chunks.append(chunk)

                    # Process the item recursively
                    self._process_json_object(item, file_path, lines, chunks, item_path, chunk.id)