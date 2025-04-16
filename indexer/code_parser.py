"""
Parser for code files.

This module was extracted from parser.py as part of modularization.
"""

import os
import logging
from typing import Optional, List, Any, Dict, Tuple
from tree_sitter import Node, Tree

from .tree_sitter_manager import TreeSitterManager
from .code_structure import CodeStructure

logger = logging.getLogger(__name__)

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
                    return self._clean_python_docstring(docstring)
        return None

    def _clean_python_docstring(self, docstring: str) -> str:
        """
        Clean up Python docstring quotes and whitespace.
        """
        docstring = docstring.strip()
        if docstring.startswith(('"""', "'''")) and docstring.endswith(('"""', "'''")):
            docstring = docstring[3:-3]
        elif docstring.startswith(("'", '"')) and docstring.endswith(("'", '"')):
            docstring = docstring[1:-1]
        return docstring.strip()

    def _process_javascript(self, node: Node, content: str, parent: CodeStructure) -> None:
        """
        Process JavaScript/TypeScript code structure
        
        Args:
            node: Root node
            content: File content
            parent: Parent code structure
        """
        # Find class definitions
        class_nodes = self._find_nodes(node, ["class_declaration"])
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
            
            # Process methods in class
            self._process_javascript_methods(class_node, content, class_struct)
            
            # Add class to parent
            parent.add_child(class_struct)
        
        # Find function declarations at module level
        function_nodes = self._find_nodes(
            node, ["function_declaration", "generator_function_declaration"], 
            exclude_parent_types=["class_declaration"]
        )
        for function_node in function_nodes:
            # Extract function name
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
        Process JavaScript/TypeScript methods in a class
        
        Args:
            class_node: Class node
            content: File content
            parent: Parent code structure
        """
        # Find method definitions
        method_nodes = self._find_nodes(class_node, ["method_definition"])
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
        Recursively find nodes of given types, optionally excluding those with certain parent types.
        """
        found = []
        exclude_parent_types = exclude_parent_types or []

        def visit(node: Node, parent_type: Optional[str] = None):
            if node.type in node_types and (not parent_type or parent_type not in exclude_parent_types):
                found.append(node)
            for child in node.children:
                visit(child, node.type)

        visit(root)
        return found

    def _find_first_node(self, root: Node, node_types: List[str]) -> Optional[Node]:
        """
        Find the first node of the given types in the subtree.
        """
        if root.type in node_types:
            return root
        for child in root.children:
            result = self._find_first_node(child, node_types)
            if result:
                return result
        return None