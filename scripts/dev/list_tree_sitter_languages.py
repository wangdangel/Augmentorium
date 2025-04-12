import tree_sitter_language_pack
from tree_sitter_language_pack import get_language, get_parser

print("Attributes of tree_sitter_language_pack:")
print(dir(tree_sitter_language_pack))

# Try to find a function that lists all languages
if hasattr(tree_sitter_language_pack, "get_all_languages"):
    langs = tree_sitter_language_pack.get_all_languages()
    print("get_all_languages():", langs)
elif hasattr(tree_sitter_language_pack, "list_languages"):
    langs = tree_sitter_language_pack.list_languages()
    print("list_languages():", langs)
else:
    print("No obvious function to list all languages found.")

# Try to call get_language with no arguments (may error)
try:
    print("get_language():", get_language())
except Exception as e:
    print("get_language() with no args error:", e)