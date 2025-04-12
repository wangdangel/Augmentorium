"""
Code parser using Tree-sitter
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Iterator
from concurrent.futures import ThreadPoolExecutor
from tree_sitter_language_pack import get_language, get_parser
from tree_sitter import Node, Tree

from utils.path_utils import get_file_extension

logger = logging.getLogger(__name__)

# Map of language names to their Tree-sitter grammars
LANGUAGE_GRAMMARS = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
    "jsx": "javascript",
    "html": "html",
    "css": "css",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "go": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "c_sharp": "c_sharp",
    "bash": "bash",
}

# Map of file extensions to language names
from indexer.language_map import EXTENSION_TO_LANGUAGE

class TreeSitterManager:
    """Manager for Tree-sitter languages and parsers"""

    def parse_file(self, file_path: str) -> Optional['Tree']:
        """
        Parse a file and return the Tree-sitter parse tree.

        Args:
            file_path: Path to the file

        Returns:
            Tree object if successful, None otherwise
        """
        try:
            language = self.detect_language(file_path)
            if not language:
                logger.warning(f"Could not detect language for file: {file_path}")
                return None
            if not self.load_language(language):
                logger.warning(f"Language '{language}' not available, cannot parse file: {file_path}")
                return None
            parser = self.parsers.get(language)
            if not parser:
                logger.warning(f"No parser found for language: {language}")
                return None
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            tree = parser.parse(bytes(content, "utf8"))
            return tree
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return None
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect programming language based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language string compatible with Tree-sitter, or None if unknown
        """
        ext = os.path.splitext(file_path)[1].lower()
        return EXTENSION_TO_LANGUAGE.get(ext)
    
    def __init__(self):
        """
        Initialize Tree-sitter manager.
        """
        self.languages: Dict[str, Any] = {}
        self.parsers: Dict[str, Any] = {}
        logger.info("Initialized Tree-sitter manager using language pack with plain text fallback.")
    
    def load_language(self, language_name: str) -> bool:
        """
        Load a Tree-sitter language using the language pack.
        Falls back to plain text if not available.
        """
        if language_name in self.languages:
            return True
        try:
            parser = get_parser(language_name)
            language = get_language(language_name)
            self.parsers[language_name] = parser
            self.languages[language_name] = language
            logger.info(f"Loaded language from language pack: {language_name}")
            return True
        except Exception as e:
            logger.warning(f"Language '{language_name}' not found in language pack, falling back to plain text: {e}")
            return False


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
        self.children: List[CodeStructure] = []
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


class CodeParser:
    """Parser for code files"""
    
    def __init__(self, tree_sitter_manager: Optional[TreeSitterManager] = None):
        """
        Initialize code parser
        
        Args:
            tree_sitter_manager: Tree-sitter manager
        """
        self.tree_sitter_manager = tree_sitter_manager or TreeSitterManager()
    
    def parse_file(self, file_path: str) -> Optional[CodeStructure]:
        """
        Parse a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[CodeStructure]: Code structure, or None if parsing failed
        """
        try:
            # Detect language
            language = self.tree_sitter_manager.detect_language(file_path)
            # Try to load language and parser
            has_grammar = language and self.tree_sitter_manager.load_language(language)

            if not has_grammar:
                logger.warning(f"Falling back to plain text for file: {file_path}")
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                lines = content.splitlines()
                root = CodeStructure(
                    node_type="plaintext",
                    name=os.path.basename(file_path),
                    start_point=(0, 0),
                    end_point=(len(lines), 0),
                    file_path=file_path,
                    language="plaintext"
                )
                root.metadata["content"] = content
                return root

            # Parse file using Tree-sitter
            tree = self.tree_sitter_manager.parse_file(file_path)
            if not tree:
                logger.warning(f"Failed to parse file: {file_path}")
                return None
            
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Process the parse tree
            root = self._process_tree(tree.root_node, content, language, file_path)
            
            return root
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return None
    
    def _process_tree(
        self,
        node: Node,
        content: str,
        language: str,
        file_path: str
    ) -> CodeStructure:
        """
        Process a parse tree
        
        Args:
            node: Root node
            content: File content
            language: Language name
            file_path: Path to the file
            
        Returns:
            CodeStructure: Root code structure
        """
        # Create root structure
        root = CodeStructure(
            node_type="module",
            name=os.path.basename(file_path),
            start_point=(0, 0),
            end_point=(node.end_point[0], node.end_point[1]),
            file_path=file_path,
            language=language
        )
        
        # Process imports
        imports = self._extract_imports(node, content, language)
        for imp in imports:
            root.add_import(imp)
        
        # Process code structure based on language
        if language == "python":
            self._process_python(node, content, root)
        elif language in ["javascript", "jsx", "typescript", "tsx"]:
            self._process_javascript(node, content, root)
        # Add more language processors as needed
        
        return root
    
    def _extract_imports(self, node: Node, content: str, language: str) -> List[str]:
        """
        Extract import statements
        
        Args:
            node: Root node
            content: File content
            language: Language name
            
        Returns:
            List[str]: List of import statements
        """
        imports = []
        
        if language == "python":
            # Find import statements in Python
            import_nodes = self._find_nodes(node, ["import_statement", "import_from_statement"])
            for import_node in import_nodes:
                import_text = content[import_node.start_byte:import_node.end_byte].strip()
                imports.append(import_text)
        
        elif language in ["javascript", "jsx", "typescript", "tsx"]:
            # Find import statements in JavaScript/TypeScript
            import_nodes = self._find_nodes(node, ["import_statement", "import_declaration"])
            for import_node in import_nodes:
                import_text = content[import_node.start_byte:import_node.end_byte].strip()
                imports.append(import_text)
        
        # Add more language-specific import extraction as needed
        
        return imports
    
    def _process_python(self, node: Node, content: str, parent: CodeStructure) -> None:
        """
        Process Python code structure
        
        Args:
            node: Root node
            content: File content
            parent: Parent code structure
        """
        # Find class definitions
        class_nodes = self._find_nodes(node, ["class_definition"])
        for class_node in class_nodes:
            # Extract class name
            name_node = self._find_first_node(class_node, ["identifier"])
            if not name_node:
                continue
            
            class_name = content[name_node.start_byte:name_node.end_byte]
            
            # Create class structure
            class_struct = CodeStructure(
                node_type="class",
                name=class_name,
                start_point=class_node.start_point,
                end_point=class_node.end_point,
                parent=parent,
                file_path=parent.file_path,
                language=parent.language
            )
            
            # Add docstring if present
            docstring = self._extract_python_docstring(class_node, content)
            if docstring:
                class_struct.set_docstring(docstring)
            
            # Process methods in class
            self._process_python_methods(class_node, content, class_struct)
            
            # Add class to parent
            parent.add_child(class_struct)
        
        # Find function definitions at module level
        function_nodes = self._find_nodes(node, ["function_definition"], 
                                        exclude_parent_types=["class_definition"])
        for function_node in function_nodes:
            # Extract function name
            name_node = self._find_first_node(function_node, ["identifier"])
            if not name_node:
                continue
            
            function_name = content[name_node.start_byte:name_node.end_byte]
            
            # Create function structure
            function_struct = CodeStructure(
                node_type="function",
                name=function_name,
                start_point=function_node.start_point,
                end_point=function_node.end_point,
                parent=parent,
                file_path=parent.file_path,
                language=parent.language
            )
            
            # Add docstring if present
            docstring = self._extract_python_docstring(function_node, content)
            if docstring:
                function_struct.set_docstring(docstring)
            
            # Add function to parent
            parent.add_child(function_struct)
    
    def _process_python_methods(self, class_node: Node, content: str, parent: CodeStructure) -> None:
        """
        Process Python methods in a class
        
        Args:
            class_node: Class node
            content: File content
            parent: Parent code structure
        """
        # Find method definitions
        method_nodes = self._find_nodes(class_node, ["function_definition"])
        for method_node in method_nodes:
            # Extract method name
            name_node = self._find_first_node(method_node, ["identifier"])
            if not name_node:
                continue
            
            method_name = content[name_node.start_byte:name_node.end_byte]
            
            # Create method structure
            method_struct = CodeStructure(
                node_type="method",
                name=method_name,
                start_point=method_node.start_point,
                end_point=method_node.end_point,
                parent=parent,
                file_path=parent.file_path,
                language=parent.language
            )
            
            # Add docstring if present
            docstring = self._extract_python_docstring(method_node, content)
            if docstring:
                method_struct.set_docstring(docstring)
            
            # Add method to parent
            parent.add_child(method_struct)
    
    def _extract_python_docstring(self, node: Node, content: str) -> Optional[str]:
        """
        Extract Python docstring
        
        Args:
            node: Node to extract docstring from
            content: File content
            
        Returns:
            Optional[str]: Docstring, or None if not found
        """
        # Find the body node
        body_node = self._find_first_node(node, ["block"])
        if not body_node:
            return None
        
        # Check if the first statement is an expression statement containing a string
        for child in body_node.children:
            if child.type == "expression_statement":
                string_node = self._find_first_node(child, ["string"])
                if string_node:
                    # Extract the docstring
                    docstring = content[string_node.start_byte:string_node.end_byte]
                    
                    # Clean up the docstring
                    docstring = self._clean_python_docstring(docstring)
                    
                    return docstring
            
            # Only check the first non-trivial child
            if child.type not in ["newline", "comment", "INDENT", "DEDENT"]:
                break
        
        return None
    
    def _clean_python_docstring(self, docstring: str) -> str:
        """
        Clean up a Python docstring
        
        Args:
            docstring: Raw docstring
            
        Returns:
            str: Cleaned docstring
        """
        # Remove quotes
        if docstring.startswith('"""') and docstring.endswith('"""'):
            docstring = docstring[3:-3]
        elif docstring.startswith("'''") and docstring.endswith("'''"):
            docstring = docstring[3:-3]
        elif docstring.startswith('"') and docstring.endswith('"'):
            docstring = docstring[1:-1]
        elif docstring.startswith("'") and docstring.endswith("'"):
            docstring = docstring[1:-1]
        
        # Remove leading indentation
        lines = docstring.split("\n")
        if len(lines) > 1:
            # Find minimum indentation
            min_indent = float("inf")
            for line in lines[1:]:
                stripped = line.lstrip()
                if stripped:  # Skip empty lines
                    indent = len(line) - len(stripped)
                    min_indent = min(min_indent, indent)
            
            if min_indent < float("inf"):
                # Remove indentation
                lines = [lines[0]] + [line[min_indent:] if line.strip() else "" for line in lines[1:]]
        
        return "\n".join(lines).strip()
    
    def _process_javascript(self, node: Node, content: str, parent: CodeStructure) -> None:
        """
        Process JavaScript/TypeScript code structure
        
        Args:
            node: Root node
            content: File content
            parent: Parent code structure
        """
        # Find class declarations
        class_nodes = self._find_nodes(node, ["class_declaration", "class", "class_expression"])
        for class_node in class_nodes:
            # Extract class name
            name_node = self._find_first_node(class_node, ["identifier"])
            if not name_node:
                continue
            
            class_name = content[name_node.start_byte:name_node.end_byte]
            
            # Create class structure
            class_struct = CodeStructure(
                node_type="class",
                name=class_name,
                start_point=class_node.start_point,
                end_point=class_node.end_point,
                parent=parent,
                file_path=parent.file_path,
                language=parent.language
            )
            
            # Process methods and properties in class
            self._process_javascript_methods(class_node, content, class_struct)
            
            # Add class to parent
            parent.add_child(class_struct)
        
        # Find function declarations
        function_nodes = self._find_nodes(
            node, 
            ["function_declaration", "function", "method_definition", "arrow_function"],
            exclude_parent_types=["class_declaration", "class", "class_expression"]
        )
        
        for function_node in function_nodes:
            # Skip anonymous functions
            name_node = self._find_first_node(function_node, ["identifier", "property_identifier"])
            if not name_node:
                continue
            
            function_name = content[name_node.start_byte:name_node.end_byte]
            
            # Create function structure
            function_struct = CodeStructure(
                node_type="function",
                name=function_name,
                start_point=function_node.start_point,
                end_point=function_node.end_point,
                parent=parent,
                file_path=parent.file_path,
                language=parent.language
            )
            
            # Add function to parent
            parent.add_child(function_struct)
    
    def _process_javascript_methods(self, class_node: Node, content: str, parent: CodeStructure) -> None:
        """
        Process JavaScript methods in a class
        
        Args:
            class_node: Class node
            content: File content
            parent: Parent code structure
        """
        # Find method definitions
        method_nodes = self._find_nodes(class_node, ["method_definition", "method"])
        for method_node in method_nodes:
            # Extract method name
            name_node = self._find_first_node(method_node, ["property_identifier", "identifier"])
            if not name_node:
                continue
            
            method_name = content[name_node.start_byte:name_node.end_byte]
            
            # Create method structure
            method_struct = CodeStructure(
                node_type="method",
                name=method_name,
                start_point=method_node.start_point,
                end_point=method_node.end_point,
                parent=parent,
                file_path=parent.file_path,
                language=parent.language
            )
            
            # Add method to parent
            parent.add_child(method_struct)
    
    def _find_nodes(
        self,
        root: Node,
        node_types: List[str],
        exclude_parent_types: Optional[List[str]] = None
    ) -> List[Node]:
        """
        Find nodes of specific types
        
        Args:
            root: Root node
            node_types: Types of nodes to find
            exclude_parent_types: Types of parent nodes to exclude
            
        Returns:
            List[Node]: Matching nodes
        """
        result = []
        exclude_parent_types = exclude_parent_types or []
        
        def visit(node: Node) -> None:
            if node.type in node_types:
                # Check if parent type should be excluded
                if exclude_parent_types:
                    parent = node.parent
                    if parent and parent.type in exclude_parent_types:
                        return
                
                result.append(node)
            
            for child in node.children:
                visit(child)
        
        visit(root)
        return result
    
    def _find_first_node(self, root: Node, node_types: List[str]) -> Optional[Node]:
        """
        Find the first node of a specific type
        
        Args:
            root: Root node
            node_types: Types of nodes to find
            
        Returns:
            Optional[Node]: First matching node, or None if not found
        """
        if root.type in node_types:
            return root
        
        for child in root.children:
            result = self._find_first_node(child, node_types)
            if result:
                return result
        
        return None
