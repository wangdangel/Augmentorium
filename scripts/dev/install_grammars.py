import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import os
import shutil
import logging
from scripts.grammar_manager import GrammarManager

logging.basicConfig(level=logging.INFO)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_build_dir = os.path.join(project_root, "grammar_build_temp")
    final_grammars_dir = os.path.join(project_root, "grammars")

    print(f"Creating temporary build directory at: {temp_build_dir}")
    os.makedirs(temp_build_dir, exist_ok=True)

    # Initialize GrammarManager with temp build dir
    gm = GrammarManager(grammar_dir=temp_build_dir)

    print("Checking system dependencies...")
    deps = gm.check_system_dependencies()
    missing = [k for k, v in deps.items() if not v]
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        gm.print_installation_instructions()
        return

    print("Installing all supported Tree-sitter grammars into temp directory...")
    successful, failed = gm.install_all_grammars()

    print("\nCopying compiled grammars to final directory...")
    os.makedirs(final_grammars_dir, exist_ok=True)

    # Copy only .dll and .so files
    for file in os.listdir(temp_build_dir):
        if file.endswith(".dll") or file.endswith(".so"):
            src = os.path.join(temp_build_dir, file)
            dst = os.path.join(final_grammars_dir, file)
            shutil.copy2(src, dst)
            print(f"Copied {file} to {final_grammars_dir}")

    print("\nCleaning up temporary build directory...")
    shutil.rmtree(temp_build_dir, ignore_errors=True)

    print("\nInstallation complete.")
    print(f"Successful grammars ({len(successful)}): {', '.join(successful)}")
    if failed:
        print(f"Failed grammars ({len(failed)}): {', '.join(failed)}")
    else:
        print("All grammars installed successfully.")

if __name__ == "__main__":
    main()
