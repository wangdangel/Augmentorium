"""
Code chunking system for Augmentorium
"""

import os
import re
import json
import json5
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Iterator, Union

from utils.path_utils import get_file_extension
from indexer.parser import CodeStructure, CodeParser

logger = logging.getLogger(__name__)

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
            logger = logging.getLogger(__name__)
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
    
    def get_strategy(self, file_path: str) -> ChunkingStrategy:
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
    
    def _create_strategy(self, strategy_name: str) -> ChunkingStrategy:
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
