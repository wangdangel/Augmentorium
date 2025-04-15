import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'indexer'))

from indexer.tree_sitter_relationships import extract_relationships_with_tree_sitter
from indexer.language_map import EXTENSION_LANGUAGE_CANDIDATES

LANG_EXAMPLES_DIR = os.path.dirname(__file__)

results = {}

for fname in os.listdir(LANG_EXAMPLES_DIR):
    if not os.path.isfile(os.path.join(LANG_EXAMPLES_DIR, fname)):
        continue
    if not any(fname.endswith(ext) for ext in EXTENSION_LANGUAGE_CANDIDATES):
        continue
    file_path = os.path.join(LANG_EXAMPLES_DIR, fname)
    try:
        relationships = extract_relationships_with_tree_sitter(file_path)
        results[fname] = relationships
    except Exception as e:
        results[fname] = f"Error: {e}"

for fname, rels in results.items():
    print(f"\n=== {fname} ===")
    if isinstance(rels, str):
        print(rels)
    else:
        for rel in rels:
            print(rel)
