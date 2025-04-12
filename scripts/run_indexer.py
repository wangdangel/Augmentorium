#!/usr/bin/env python3
print("Running script at:", __file__)
"""
Standalone script to run the Augmentorium indexer during development
"""

import os
import sys
import time
import logging
import argparse

# Determine the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to the Python path if not already added
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now attempt to import
try:
    from config.manager import ConfigManager
    from utils.logging import setup_logging
    from indexer.indexer_init import start_indexer
except ImportError as e:
    print(f"Import error: {e}")
    print("\nTroubleshooting steps:")
    print("1. Ensure you're in the virtual environment")
    print("2. Run 'pip install -e .' in the project root")
    print("3. Verify the package structure")
    print(f"\nCurrent Python path: {sys.path}")
    sys.exit(1)

def main():
    """Main entry point for the indexer"""
    parser = argparse.ArgumentParser(description="Augmentorium Indexer")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--projects", help="Comma-separated list of project paths to index")
    parser.add_argument("--ollama-url", default="http://localhost:11434", 
                        help="URL for the Ollama API")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                      default="INFO", help="Set the logging level")
    args = parser.parse_args()
    
    config_path = os.path.abspath(args.config or "config.yaml")
    print(f"DEBUG: Using config_path = {config_path}")
    # Load configuration first
    config = ConfigManager(config_path)
    
    # Setup logging using config value
    log_level = getattr(logging, config.config.get("general", {}).get("log_level", "INFO"))
    setup_logging(log_level)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.info("Starting Augmentorium Indexer")
    logger.debug(f"Using config path: {config_path}")
    
    # Log the Ollama API URL being used from the config file
    logger.info(f"Using Ollama API from config: {config.config['ollama'].get('base_url', 'Default missing')}")

    # Get project paths
    project_paths = args.projects.split(",") if args.projects else None
    
    # Start indexer
    logger.info("Starting indexer service...")
    service = start_indexer(config, project_paths)
    
    # Keep running
    try:
        logger.info("Indexer service started. Press Ctrl+C to stop.")
        print("Indexer service started. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping indexer service")
        service.stop()
        logger.info("Indexer service stopped.")

if __name__ == "__main__":
    main()
