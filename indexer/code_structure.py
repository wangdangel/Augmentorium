"""
Representation of code structure.

This module was extracted from parser.py as part of modularization.
"""

from typing import Optional, List, Set, Dict, Any, Tuple

class CodeStructure:
    """Representation of code structure"""
    
    def __init__(
        self,
        node_type: str,
        name: Optional[str],
        start_point: Tuple[int, int],
        end_point: Tuple[int, int],
        parent: Optional['CodeStructure'] = None,
        file_path: Optional[str] = None,
        language: Optional[str] = None
    ):
        """
        Initialize code structure
        
        Args:
            node_type: Type of node (function, class, etc.)
            name: Name of the node
            start_point: Start position (line, column)
            end_point: End position (line, column)
            parent: Parent node
            file_path: Path to the file
            language: Language of the code
        """
        self.node_type = node_type
        self.name = name
        self.start_point = start_point
        self.end_point = end_point
        self.parent = parent
        self.file_path = file_path
        self.language = language
        self.children: List['CodeStructure'] = []
        self.imports: List[str] = []
        self.references: Set[str] = set()
        self.docstring: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    def add_child(self, child: 'CodeStructure') -> None:
        """Add a child node"""
        child.parent = self
        self.children.append(child)
    
    def add_import(self, import_name: str) -> None:
        """Add an import statement"""
        if import_name not in self.imports:
            self.imports.append(import_name)
    
    def add_reference(self, reference: str) -> None:
        """Add a reference to another entity"""
        self.references.add(reference)
    
    def set_docstring(self, docstring: str) -> None:
        """Set the docstring"""
        self.docstring = docstring
    
    def get_full_name(self) -> str:
        """
        Get the full name including parent names
        
        Returns:
            str: Full name
        """
        if self.parent and self.parent.name:
            return f"{self.parent.get_full_name()}.{self.name}"
        return self.name or ""
    
    def get_path(self) -> str:
        """
        Get the path in the code structure
        
        Returns:
            str: Path in the code structure
        """
        if self.parent:
            parent_path = self.parent.get_path()
            if parent_path:
                return f"{parent_path}/{self.node_type}:{self.name}"
        return f"{self.node_type}:{self.name}"
    
    def get_line_range(self) -> Tuple[int, int]:
        """
        Get the line range
        
        Returns:
            Tuple[int, int]: Start and end line numbers
        """
        return (self.start_point[0], self.end_point[0])
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "node_type": self.node_type,
            "name": self.name,
            "full_name": self.get_full_name(),
            "path": self.get_path(),
            "start_line": self.start_point[0],
            "end_line": self.end_point[0],
            "file_path": self.file_path,
            "language": self.language,
            "imports": self.imports,
            "references": list(self.references),
            "docstring": self.docstring,
            "metadata": self.metadata,
            "children": [child.to_dict() for child in self.children]
        }
    
    def __str__(self) -> str:
        return f"{self.node_type}:{self.name} ({self.start_point[0]}-{self.end_point[0]})"