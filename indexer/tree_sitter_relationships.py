"""
Extract code relationships (imports, inheritance, includes, etc.) from source files using Tree-sitter for all supported languages.
"""
import os
from typing import List, Dict
from indexer.tree_sitter_manager import TreeSitterManager

import logging
logger = logging.getLogger(__name__)

def walk_tree(cursor):
    """Yield every node in the tree, depth-first, starting from the cursor's node."""
    visited = set()
    while True:
        node = cursor.node
        if id(node) not in visited:
            yield node
            visited.add(id(node))
        if cursor.goto_first_child():
            continue
        if cursor.goto_next_sibling():
            continue
        retracing = True
        while retracing:
            if not cursor.goto_parent():
                return
            if cursor.goto_next_sibling():
                retracing = False

def extract_relationships_with_tree_sitter(file_path: str) -> List[Dict]:
    """
    Extract code relationships (imports, inheritance, includes, etc.) from a source file using Tree-sitter.
    Returns a list of dicts: {"target": ..., "type": ...}
    """
    relationships = []
    manager = TreeSitterManager()
    language = manager.detect_language(file_path)
    logger.info(f"[DEBUG] Detected language for {file_path}: {language}")
    logger.info(f"[DEBUG] Available grammars: {getattr(manager, 'LANGUAGE_GRAMMARS', getattr(manager, 'language_grammars', 'UNKNOWN'))}")
    if not language:
        logger.warning(f"Could not detect language for file: {file_path}")
        return relationships
    tree = manager.parse_file(file_path)
    if not tree:
        logger.warning(f"Could not parse file: {file_path}")
        return relationships

    # Read file content for node text extraction
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        code = f.read()
    
    # Helper to get node text
    def get_node_text(node):
        return code[node.start_byte:node.end_byte]

    # Language-specific queries
    root = tree.root_node
    cursor = tree.walk()
    if language == "python":
        for node in walk_tree(cursor):
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        relationships.append({"target": get_node_text(child), "type": "import"})
                    elif child.type == "alias":
                        for alias_child in child.children:
                            if alias_child.type == "identifier":
                                relationships.append({"target": get_node_text(alias_child), "type": "import"})
            elif node.type == "import_from_statement":
                module = None
                names = []
                for child in node.children:
                    if child.type == "dotted_name":
                        module = get_node_text(child)
                    elif child.type == "import_list":
                        for name_node in child.children:
                            if name_node.type == "identifier":
                                names.append(get_node_text(name_node))
                if module and names:
                    for name in names:
                        relationships.append({"target": f"{module}.{name}", "type": "import"})
                elif module:
                    relationships.append({"target": module, "type": "import"})
            elif node.type == "class_definition":
                for child in node.children:
                    if child.type == "argument_list":
                        for base in child.children:
                            if base.type == "identifier":
                                relationships.append({"target": get_node_text(base), "type": "inherits"})
    elif language in ("javascript", "typescript", "tsx", "jsx"):
        for node in root.children:
            if node.type == "import_statement":
                found = False
                for child in node.children:
                    if child.type == "string":
                        relationships.append({"target": get_node_text(child).strip('"\''), "type": "import"})
                        found = True
                if not found:
                    text = get_node_text(node)
                    import re
                    m = re.search(r"from\s+['\"]([^'\"]+)['\"]", text)
                    if m:
                        relationships.append({"target": m.group(1), "type": "import"})
                        found = True
                    if not found:
                        m2 = re.search(r"import\s+['\"]([^'\"]+)['\"]", text)
                        if m2:
                            relationships.append({"target": m2.group(1), "type": "import"})
                    if not found:
                        m3 = re.findall(r"['\"]([^'\"]+)['\"]", text)
                        if m3:
                            relationships.append({"target": m3[-1], "type": "import"})
            elif node.type == "call_expression":
                callee = node.child_by_field_name("function")
                if callee and get_node_text(callee) == "require":
                    arg = node.child_by_field_name("arguments")
                    if arg and len(arg.children) > 1:
                        literal = arg.children[1]
                        if literal.type == "string":
                            relationships.append({"target": get_node_text(literal).strip('"\''), "type": "import"})
            elif node.type == "class_declaration":
                for child in node.children:
                    if child.type == "class_heritage":
                        for base in child.children:
                            if base.type == "identifier":
                                relationships.append({"target": get_node_text(base), "type": "inherits"})
    elif language == "java":
        for node in walk_tree(cursor):
            if node.type == "import_declaration":
                for child in node.children:
                    if child.type == "scoped_identifier":
                        relationships.append({"target": get_node_text(child), "type": "import"})
            elif node.type == "class_declaration":
                for child in node.children:
                    if child.type == "superclass":
                        for base in child.children:
                            if base.type == "type_identifier":
                                relationships.append({"target": get_node_text(base), "type": "inherits"})
    elif language in ("c", "cpp", "c++", "cxx", "h", "hpp"):
        for node in walk_tree(cursor):
            if node.type == "preproc_include":
                for child in node.children:
                    if child.type == "string":
                        relationships.append({"target": get_node_text(child).strip('"<>'), "type": "include"})
            elif node.type == "class_specifier":
                for child in node.children:
                    if child.type == "base_class_clause":
                        for base in child.children:
                            if base.type == "type_identifier":
                                relationships.append({"target": get_node_text(base), "type": "inherits"})
    elif language == "go":
        for node in walk_tree(cursor):
            if node.type == "import_spec":
                for child in node.children:
                    if child.type == "interpreted_string_literal":
                        relationships.append({"target": get_node_text(child).strip('"'), "type": "import"})
    elif language == "rust":
        for node in walk_tree(cursor):
            if node.type == "use_declaration":
                for child in node.children:
                    if child.type == "scoped_use_list" or child.type == "use_list":
                        for use_item in child.children:
                            if use_item.type == "scoped_identifier" or use_item.type == "identifier":
                                relationships.append({"target": get_node_text(use_item), "type": "import"})
                    elif child.type == "scoped_identifier" or child.type == "identifier":
                        relationships.append({"target": get_node_text(child), "type": "import"})
    elif language == "php":
        for node in walk_tree(cursor):
            if node.type == "namespace_use_declaration":
                for child in node.children:
                    if child.type == "namespace_name":
                        relationships.append({"target": get_node_text(child), "type": "import"})
            elif node.type == "require_expression" or node.type == "include_expression":
                for child in node.children:
                    if child.type == "string":
                        relationships.append({"target": get_node_text(child).strip('"\''), "type": "import"})
    elif language == "ruby":
        for node in walk_tree(cursor):
            if node.type == "call":
                method = node.child_by_field_name("method")
                if method and get_node_text(method) in ("require", "require_relative", "load"):
                    arg = node.child_by_field_name("argument")
                    if arg and arg.type == "string":
                        relationships.append({"target": get_node_text(arg).strip('"\''), "type": "import"})
    elif language == "kotlin":
        for node in walk_tree(cursor):
            if node.type == "import_header":
                for child in node.children:
                    if child.type == "identifier" or child.type == "scoped_identifier":
                        relationships.append({"target": get_node_text(child), "type": "import"})
    elif language == "scala":
        for node in walk_tree(cursor):
            if node.type == "import":
                for child in node.children:
                    if child.type == "import_expr":
                        relationships.append({"target": get_node_text(child), "type": "import"})
    elif language == "dart":
        for node in walk_tree(cursor):
            if node.type == "import_or_export":
                for child in node.children:
                    if child.type == "uri":
                        relationships.append({"target": get_node_text(child).strip('"\''), "type": "import"})
    elif language == "swift":
        for node in walk_tree(cursor):
            if node.type == "import_declaration":
                for child in node.children:
                    if child.type == "import_path":
                        relationships.append({"target": get_node_text(child), "type": "import"})
    elif language == "bash":
        for node in walk_tree(cursor):
            if node.type == "source_command":
                for child in node.children:
                    if child.type == "string" or child.type == "word":
                        relationships.append({"target": get_node_text(child), "type": "source"})
    elif language == "r":
        for node in walk_tree(cursor):
            if node.type == "library_call":
                for child in node.children:
                    if child.type == "string":
                        relationships.append({"target": get_node_text(child).strip('"\''), "type": "import"})
    elif language == "matlab":
        for node in walk_tree(cursor):
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "identifier":
                        relationships.append({"target": get_node_text(child), "type": "import"})
    elif language == "perl":
        for node in walk_tree(cursor):
            if node.type == "use_statement" or node.type == "require_statement":
                for child in node.children:
                    if child.type == "identifier" or child.type == "string":
                        relationships.append({"target": get_node_text(child).strip('"\''), "type": "import"})
    elif language == "groovy":
        for node in walk_tree(cursor):
            if node.type == "import_declaration":
                for child in node.children:
                    if child.type == "scoped_identifier" or child.type == "identifier":
                        relationships.append({"target": get_node_text(child), "type": "import"})
    elif language in ("c_sharp", "csharp"):
        for node in walk_tree(cursor):
            if node.type == "using_directive":
                for child in node.children:
                    if child.type in ("name_equals", "identifier", "qualified_name"):
                        relationships.append({"target": get_node_text(child), "type": "import"})

    return relationships
