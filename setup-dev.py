#!/usr/bin/env python3
"""
Development setup script for Augmentorium
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def create_virtual_env(venv_path, force=False):
    """Create a virtual environment"""
    if os.path.exists(venv_path) and not force:
        print(f"Virtual environment already exists at {venv_path}")
        return True

    try:
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print(f"Created virtual environment at {venv_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        return False

def install_dependencies(venv_path, dev_mode=True):
    """Install dependencies"""
    # Get the python and pip executables from the virtual environment
    if os.name == 'nt':  # Windows
        python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
        pip_exe = os.path.join(venv_path, 'Scripts', 'pip.exe')
    else:  # Unix/Linux/MacOS
        python_exe = os.path.join(venv_path, 'bin', 'python')
        pip_exe = os.path.join(venv_path, 'bin', 'pip')

    try:
        # Upgrade pip
        subprocess.run([pip_exe, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        print("Installing requirements...")
        subprocess.run([pip_exe, "install", "-r", "requirements.txt"], check=True)
        
        # Install the package in development mode
        if dev_mode:
            print("Installing Augmentorium in development mode...")
            subprocess.run([pip_exe, "install", "-e", "."], check=True)
        else:
            print("Installing Augmentorium...")
            subprocess.run([pip_exe, "install", "."], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def create_dev_config():
    """Create development configuration"""
    home_dir = str(Path.home())
    config_dir = os.path.join(home_dir, ".augmentorium")
    
    # Ensure config directory exists
    os.makedirs(config_dir, exist_ok=True)
    
    # Create logs directory
    logs_dir = os.path.join(config_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    print(f"Created development configuration at {config_dir}")
    return True

def create_run_scripts(venv_path, output_dir):
    """Create scripts to run the application in development mode"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the python executable from the virtual environment
    if os.name == 'nt':  # Windows
        python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
        ext = '.bat'
        script_prefix = '@echo off\r\n'
        activate_cmd = f'call "{os.path.join(venv_path, "Scripts", "activate.bat")}"\r\n'
    else:  # Unix/Linux/MacOS
        python_exe = os.path.join(venv_path, 'bin', 'python')
        ext = '.sh'
        script_prefix = '#!/bin/bash\n'
        activate_cmd = f'source "{os.path.join(venv_path, "bin", "activate")}"\n'
    
    # Create run_indexer script
    indexer_script = os.path.join(output_dir, f"run_indexer{ext}")
    with open(indexer_script, 'w') as f:
        f.write(script_prefix)
        f.write(activate_cmd)
        f.write(f'python -m augmentorium.indexer --log-level DEBUG "$@"\n')
    
    # Create run_server script
    server_script = os.path.join(output_dir, f"run_server{ext}")
    with open(server_script, 'w') as f:
        f.write(script_prefix)
        f.write(activate_cmd)
        f.write(f'python -m augmentorium.server --log-level DEBUG "$@"\n')
    
    # Make scripts executable on Unix/Linux/MacOS
    if os.name != 'nt':
        os.chmod(indexer_script, 0o755)
        os.chmod(server_script, 0o755)
    
    print(f"Created run scripts in {output_dir}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Set up Augmentorium for development")
    parser.add_argument("--venv", default=".venv", help="Path to virtual environment")
    parser.add_argument("--force", action="store_true", help="Force recreation of virtual environment")
    parser.add_argument("--no-dev", action="store_true", help="Install in normal mode instead of development mode")
    args = parser.parse_args()
    
    # Create virtual environment
    if not create_virtual_env(args.venv, args.force):
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(args.venv, not args.no_dev):
        sys.exit(1)
    
    # Create development configuration
    if not create_dev_config():
        sys.exit(1)
    
    # Create run scripts
    if not create_run_scripts(args.venv, "scripts/dev"):
        sys.exit(1)
    
    print("\nSetup complete! To run Augmentorium in development mode:")
    print(f"1. Start the indexer: scripts/dev/run_indexer{'.bat' if os.name == 'nt' else '.sh'}")
    print(f"2. Start the server: scripts/dev/run_server{'.bat' if os.name == 'nt' else '.sh'}")

if __name__ == "__main__":
    main()
