"""
NOTE: This file has been modularized. All core logic has been moved to:
    - indexer/language_grammars.py
    - indexer/tree_sitter_manager.py
    - indexer/code_structure.py
    - indexer/code_parser.py

This file is pending removal after migration is validated. Please update all imports to use the new modules.

Legacy imports for backward compatibility:
"""

from indexer.language_grammars import LANGUAGE_GRAMMARS
from indexer.tree_sitter_manager import TreeSitterManager
from indexer.code_structure import CodeStructure
from indexer.code_parser import CodeParser
