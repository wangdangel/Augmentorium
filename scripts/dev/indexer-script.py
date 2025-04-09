#!/usr/bin/env python3
"""
Development script to run the Augmentorium indexer
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from augmentorium.config.manager import ConfigManager
from augmentorium.utils.logging import setup_logging
from augmentorium.indexer import start_indexer

def main():
    """Main entry point for development indexer"""
    parser = argparse.ArgumentParser(description="Augmentorium Indexer (Development)")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--projects", help="Comma-separated list of project paths to index")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="DEBUG",
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.info("Starting Augmentorium Indexer in development mode")
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Get project paths
    project_paths = args.projects.split(",") if args.projects else None
    
    # Start indexer
    service = start_indexer(config, project_paths)
    
    # Keep running
    try:
        logger.info("Indexer service started. Press Ctrl+C to stop.")
        print("Indexer service started. Press Ctrl+C to stop.")
        
        # Simple way to keep the script running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping indexer service")
        service.stop()
        logger.info("Indexer service stopped")

if __name__ == "__main__":
    main()
