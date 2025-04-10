#!/usr/bin/env python3
"""
Standalone script to run the Augmentorium server during development
"""

import os
import sys
import time
import logging
import argparse

# Add the project root to the Python path if not already added
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import local modules
from config.manager import ConfigManager
from utils.logging import setup_logging
from server.server_init import start_api_server

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Augmentorium Server")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--project", help="Path to the active project")
    parser.add_argument("--port", type=int, default=6655, help="Port for the API server")
    parser.add_argument("--ollama-url", help="URL for the Ollama API (e.g., http://server-ip:11434)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                      default="DEBUG", help="Set the logging level")
    return parser.parse_args()

def main():
    """Main entry point for the server"""
    args = parse_arguments()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Augmentorium Server")
    
    config = ConfigManager(args.config)
    
    if args.ollama_url:
        config.global_config.setdefault('ollama', {})['base_url'] = args.ollama_url
        logger.info(f"Using Ollama API at: {args.ollama_url}")
    
    api_server, api_thread = start_api_server(config, args.port, args.project)
    
    try:
        logger.info("Server started. Press Ctrl+C to stop.")
        print("Server started. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping server")
        logger.info("Server stopped.")

if __name__ == "__main__":
    main()
