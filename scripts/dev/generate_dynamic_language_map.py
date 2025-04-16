import os
import glob

# Path to the tree_sitter_language_pack bindings directory
BINDINGS_PATH = r'K:\Documents\augmentorium\.venv\Lib\site-packages\tree_sitter_language_pack\bindings'

def get_available_languages():
    langs = []
    for fname in os.listdir(BINDINGS_PATH):
        if fname.endswith('.pyd') and not fname.startswith('__'):
            langs.append(os.path.splitext(fname)[0])
    return sorted(langs)

if __name__ == "__main__":
    langs = get_available_languages()
    print("Available tree-sitter grammars (language names):")
    for lang in langs:
        print(lang)
    print(f"Total: {len(langs)} languages")