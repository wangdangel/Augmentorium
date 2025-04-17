import os
import shutil
import filecmp
from pathlib import Path

MAIN_DIR = Path(r'k:/Documents/augmentorium')
RELEASE_DIR = Path(r'k:/Documents/augmentorium_release')

IGNORED_KEYWORDS = ['depth', '.git', '.qodo', 'qodo']  # case-insensitive

def should_ignore(path: Path) -> bool:
    path_str = str(path).lower().replace('\\', '/').replace('/', '/')
    return any(keyword in path_str for keyword in IGNORED_KEYWORDS)

def prompt_user(src, dst):
    while True:
        response = input(f"Copy {src} -> {dst}? [y/n]: ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("Please enter 'y' or 'n'.")

def sync_file(rel_path: Path):
    src = MAIN_DIR / rel_path
    dst = RELEASE_DIR / rel_path
    if should_ignore(src) or should_ignore(dst):
        print(f"Ignoring (excluded): {src}")
        return
    if not src.exists() or not dst.exists():
        # Only process files that exist in BOTH folders
        return
    if src.is_file() and dst.is_file():
        if not filecmp.cmp(src, dst, shallow=False):
            if prompt_user(src, dst):
                print(f"Copying {src} -> {dst}")
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            else:
                print(f"Skipped: {src}")
        else:
            print(f"No change: {src}")
    elif src.is_dir() and dst.is_dir():
        for item in dst.iterdir():
            sync_file(rel_path / item.name)

def main():
    for root, dirs, files in os.walk(RELEASE_DIR):
        rel_root = Path(root).relative_to(RELEASE_DIR)
        for file in files:
            rel_path = rel_root / file
            sync_file(rel_path)

if __name__ == '__main__':
    main()
