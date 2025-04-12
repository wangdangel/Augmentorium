import os
from tree_sitter_language_pack import get_language

BINDINGS_PATH = r'K:\Documents\augmentorium\.venv\Lib\site-packages\tree_sitter_language_pack\bindings'

def get_available_languages():
    langs = []
    for fname in os.listdir(BINDINGS_PATH):
        if fname.endswith('.pyd') and not fname.startswith('__'):
            langs.append(os.path.splitext(fname)[0])
    return sorted(langs)

def validate_languages(langs):
    valid = []
    invalid = []
    for lang in langs:
        try:
            get_language(lang)
            valid.append(lang)
        except Exception as e:
            invalid.append((lang, str(e)))
    return valid, invalid

if __name__ == "__main__":
    langs = get_available_languages()
    valid, invalid = validate_languages(langs)
    print("Valid languages (can be loaded):")
    for lang in valid:
        print(lang)
    print(f"\nTotal valid: {len(valid)}")
    if invalid:
        print("\nInvalid or failed to load:")
        for lang, err in invalid:
            print(f"{lang}: {err}")
        print(f"\nTotal invalid: {len(invalid)}")