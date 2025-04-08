"""
Grammar manager for Tree-sitter
"""

import os
import sys
import shutil
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Map of language names to their GitHub repositories
LANGUAGE_REPOS = {
    "python": "https://github.com/tree-sitter/tree-sitter-python",
    "javascript": "https://github.com/tree-sitter/tree-sitter-javascript",
    "typescript": "https://github.com/tree-sitter/tree-sitter-typescript",
    "tsx": "https://github.com/tree-sitter/tree-sitter-typescript",
    "html": "https://github.com/tree-sitter/tree-sitter-html",
    "css": "https://github.com/tree-sitter/tree-sitter-css",
    "java": "https://github.com/tree-sitter/tree-sitter-java",
    "c": "https://github.com/tree-sitter/tree-sitter-c",
    "cpp": "https://github.com/tree-sitter/tree-sitter-cpp",
    "go": "https://github.com/tree-sitter/tree-sitter-go",
    "rust": "https://github.com/tree-sitter/tree-sitter-rust",
    "ruby": "https://github.com/tree-sitter/tree-sitter-ruby",
    "php": "https://github.com/tree-sitter/tree-sitter-php",
    "c_sharp": "https://github.com/tree-sitter/tree-sitter-c-sharp",
    "bash": "https://github.com/tree-sitter/tree-sitter-bash",
}

# Map of language names to their pre-built binary URLs (can be expanded later)
PREBUILT_URLS = {
    # Format: "language": "URL to prebuilt .so/.dll file"
}

class GrammarManager:
    """Manager for Tree-sitter grammars"""
    
    def __init__(self, grammar_dir: Optional[str] = None):
        """
        Initialize grammar manager
        
        Args:
            grammar_dir: Directory to store grammars
        """
        # Set default grammar directory
        if grammar_dir is None:
            home_dir = str(Path.home())
            grammar_dir = os.path.join(home_dir, ".augmentorium", "tree-sitter-grammars")
        
        self.grammar_dir = grammar_dir
        os.makedirs(self.grammar_dir, exist_ok=True)
        
        # Initialize installed grammars
        self.installed_grammars = self._get_installed_grammars()
        
        logger.info(f"Initialized grammar manager with directory: {self.grammar_dir}")
        logger.info(f"Found {len(self.installed_grammars)} installed grammars")
    
    def _get_installed_grammars(self) -> Set[str]:
        """
        Get set of installed grammars
        
        Returns:
            Set[str]: Set of installed grammar names
        """
        installed = set()
        
        # Check for .so files (Linux/macOS) or .dll files (Windows)
        extensions = [".so", ".dll"]
        
        for file in os.listdir(self.grammar_dir):
            name, ext = os.path.splitext(file)
            if ext in extensions:
                installed.add(name)
        
        return installed
    
    def is_grammar_installed(self, grammar: str) -> bool:
        """
        Check if a grammar is installed
        
        Args:
            grammar: Name of the grammar
            
        Returns:
            bool: True if installed, False otherwise
        """
        return grammar in self.installed_grammars
    
    def get_grammar_path(self, grammar: str) -> Optional[str]:
        """
        Get path to a grammar library
        
        Args:
            grammar: Name of the grammar
            
        Returns:
            Optional[str]: Path to the grammar, or None if not installed
        """
        if not self.is_grammar_installed(grammar):
            return None
        
        # Check for .so files (Linux/macOS) or .dll files (Windows)
        extensions = [".so", ".dll"]
        
        for ext in extensions:
            path = os.path.join(self.grammar_dir, f"{grammar}{ext}")
            if os.path.exists(path):
                return path
        
        return None
    
    def install_grammar(self, grammar: str) -> bool:
        """
        Install a grammar
        
        Args:
            grammar: Name of the grammar
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.is_grammar_installed(grammar):
            logger.info(f"Grammar {grammar} is already installed")
            return True
        
        logger.info(f"Installing grammar: {grammar}")
        
        # Try downloading pre-built grammar
        if self._download_prebuilt_grammar(grammar):
            self.installed_grammars.add(grammar)
            return True
        
        # Fall back to building from source
        if self._build_grammar(grammar):
            self.installed_grammars.add(grammar)
            return True
        
        logger.error(f"Failed to install grammar: {grammar}")
        return False
    
    def install_all_grammars(self) -> Tuple[List[str], List[str]]:
        """
        Install all supported grammars
        
        Returns:
            Tuple[List[str], List[str]]: Lists of successful and failed grammars
        """
        successful = []
        failed = []
        
        for grammar in tqdm(LANGUAGE_REPOS.keys(), desc="Installing grammars"):
            if self.install_grammar(grammar):
                successful.append(grammar)
            else:
                failed.append(grammar)
        
        return successful, failed
    
    def _download_prebuilt_grammar(self, grammar: str) -> bool:
        """
        Download a pre-built grammar
        
        Args:
            grammar: Name of the grammar
            
        Returns:
            bool: True if successful, False otherwise
        """
        if grammar not in PREBUILT_URLS:
            logger.debug(f"No pre-built grammar available for {grammar}")
            return False
        
        url = PREBUILT_URLS[grammar]
        
        try:
            logger.info(f"Downloading pre-built grammar for {grammar} from {url}")
            
            # Determine file extension based on platform
            if sys.platform.startswith("win"):
                ext = ".dll"
            else:
                ext = ".so"
            
            # Download file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save to file
            with open(os.path.join(self.grammar_dir, f"{grammar}{ext}"), "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded pre-built grammar for {grammar}")
            return True
        except Exception as e:
            logger.warning(f"Failed to download pre-built grammar for {grammar}: {e}")
            return False
    
    def _build_grammar(self, grammar: str) -> bool:
        """
        Build a grammar from source
        
        Args:
            grammar: Name of the grammar
            
        Returns:
            bool: True if successful, False otherwise
        """
        if grammar not in LANGUAGE_REPOS:
            logger.error(f"No repository available for grammar: {grammar}")
            return False
        
        repo_url = LANGUAGE_REPOS[grammar]
        
        try:
            logger.info(f"Building grammar {grammar} from {repo_url}")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone repository
                logger.debug(f"Cloning repository: {repo_url}")
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, temp_dir],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Special handling for TypeScript/TSX
                if grammar == "tsx":
                    # For TSX, we need to cd into the tsx directory
                    build_dir = os.path.join(temp_dir, "tsx")
                    if not os.path.exists(build_dir):
                        logger.error(f"TSX directory not found in {temp_dir}")
                        return False
                elif grammar == "typescript":
                    # For TypeScript, we need to cd into the typescript directory
                    build_dir = os.path.join(temp_dir, "typescript")
                    if not os.path.exists(build_dir):
                        logger.error(f"TypeScript directory not found in {temp_dir}")
                        return False
                else:
                    build_dir = temp_dir
                
                # Build using tree-sitter CLI
                logger.debug(f"Building grammar in {build_dir}")
                subprocess.run(
                    ["tree-sitter", "generate"],
                    cwd=build_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Compile shared library
                logger.debug("Compiling shared library")
                subprocess.run(
                    ["tree-sitter", "build-wasm"],
                    cwd=build_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Determine output file
                if sys.platform.startswith("win"):
                    # Windows
                    src_path = os.path.join(build_dir, f"{grammar}.dll")
                    if not os.path.exists(src_path):
                        src_path = os.path.join(build_dir, "build", f"{grammar}.dll")
                    dst_path = os.path.join(self.grammar_dir, f"{grammar}.dll")
                else:
                    # Linux/macOS
                    src_path = os.path.join(build_dir, f"libtree-sitter-{grammar}.so")
                    if not os.path.exists(src_path):
                        src_path = os.path.join(build_dir, "build", f"libtree-sitter-{grammar}.so")
                    dst_path = os.path.join(self.grammar_dir, f"{grammar}.so")
                
                # Check if file exists
                if not os.path.exists(src_path):
                    logger.error(f"Built grammar file not found: {src_path}")
                    logger.debug("Trying alternative build paths...")
                    
                    # Try scanning for the file
                    for root, _, files in os.walk(build_dir):
                        for file in files:
                            if file.endswith(".so") or file.endswith(".dll"):
                                logger.debug(f"Found potential grammar file: {os.path.join(root, file)}")
                                src_path = os.path.join(root, file)
                                break
                
                # Copy to grammar directory
                logger.debug(f"Copying {src_path} to {dst_path}")
                shutil.copy(src_path, dst_path)
            
            logger.info(f"Successfully built grammar: {grammar}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.cmd}")
            logger.error(f"Output: {e.stdout.decode() if e.stdout else ''}")
            logger.error(f"Error: {e.stderr.decode() if e.stderr else ''}")
            return False
        except Exception as e:
            logger.error(f"Failed to build grammar {grammar}: {e}")
            return False
    
    def check_tree_sitter_cli(self) -> bool:
        """
        Check if tree-sitter CLI is installed
        
        Returns:
            bool: True if installed, False otherwise
        """
        try:
            subprocess.run(
                ["tree-sitter", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_system_dependencies(self) -> Dict[str, bool]:
        """
        Check system dependencies for building grammars
        
        Returns:
            Dict[str, bool]: Dictionary of dependencies and their availability
        """
        dependencies = {
            "git": False,
            "tree-sitter": False,
            "gcc/clang": False,
            "python-dev": False,
        }
        
        # Check git
        try:
            subprocess.run(
                ["git", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            dependencies["git"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check tree-sitter CLI
        dependencies["tree-sitter"] = self.check_tree_sitter_cli()
        
        # Check compiler
        try:
            if sys.platform.startswith("win"):
                compiler_cmd = ["cl"]
            else:
                compiler_cmd = ["gcc", "--version"]
            
            subprocess.run(
                compiler_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            dependencies["gcc/clang"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try clang as alternative
            if not sys.platform.startswith("win"):
                try:
                    subprocess.run(
                        ["clang", "--version"],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    dependencies["gcc/clang"] = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
        
        # Check for Python development headers
        try:
            if sys.platform.startswith("win"):
                python_include = os.path.join(sys.prefix, "include")
                dependencies["python-dev"] = os.path.exists(python_include)
            else:
                import distutils.sysconfig
                python_include = distutils.sysconfig.get_python_inc()
                dependencies["python-dev"] = os.path.exists(os.path.join(python_include, "Python.h"))
        except:
            pass
        
        return dependencies
    
    def print_installation_instructions(self) -> None:
        """Print instructions for installing dependencies"""
        dependencies = self.check_system_dependencies()
        missing = [dep for dep, installed in dependencies.items() if not installed]
        
        if not missing:
            logger.info("All dependencies are installed")
            return
        
        logger.warning(f"Missing dependencies: {', '.join(missing)}")
        print("\nTo build Tree-sitter grammars, you need to install the following dependencies:\n")
        
        if "git" in missing:
            print("- Git: https://git-scm.com/downloads")
            if sys.platform.startswith("linux"):
                print("  sudo apt-get install git")
            elif sys.platform.startswith("darwin"):
                print("  brew install git")
        
        if "tree-sitter" in missing:
            print("- Tree-sitter CLI: https://tree-sitter.github.io/tree-sitter/")
            print("  npm install -g tree-sitter-cli")
        
        if "gcc/clang" in missing:
            print("- C compiler (gcc or clang):")
            if sys.platform.startswith("linux"):
                print("  sudo apt-get install build-essential")
            elif sys.platform.startswith("darwin"):
                print("  xcode-select --install")
            elif sys.platform.startswith("win"):
                print("  Install Visual Studio with C++ build tools")
        
        if "python-dev" in missing:
            print("- Python development headers:")
            if sys.platform.startswith("linux"):
                print(f"  sudo apt-get install python{sys.version_info.major}.{sys.version_info.minor}-dev")
            elif sys.platform.startswith("darwin"):
                print("  Usually included with Python installation from python.org or brew")
            elif sys.platform.startswith("win"):
                print("  Usually included with Python installation from python.org")
