#!/usr/bin/env python3
"""
Standalone script to run the Augmentorium indexer
"""

import os
import sys
import time
import logging
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from the augmentorium package
from augmentorium.config.manager import ConfigManager
from augmentorium.utils.logging import setup_logging
from augmentorium.indexer.indexer_init import start_indexer

def main():
    """Main entry point for the indexer"""
    parser = argparse.ArgumentParser(description="Augmentorium Indexer")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--projects", help="Comma-separated list of project paths to index")
    parser.add_argument("--ollama-url", help="URL for the Ollama API (e.g., http://server-ip:11434)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                      default="DEBUG", help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.info("Starting Augmentorium Indexer")
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Get project paths
    project_paths = args.projects.split(",") if args.projects else None
    
    # Update Ollama URL if specified
    if args.ollama_url:
        if 'ollama' not in config.global_config:
            config.global_config['ollama'] = {}
        config.global_config['ollama']['base_url'] = args.ollama_url
        logger.info(f"Using Ollama API at: {args.ollama_url}")
    
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
        logger.info("Stopping indexer service...")
        service.stop()
        logger.info("Indexer service stopped.")

if __name__ == "__main__":
    main()