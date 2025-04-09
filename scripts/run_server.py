#!/usr/bin/env python3
"""
Standalone script to run the Augmentorium MCP server
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
from augmentorium.server.server_init import start_server

def main():
    """Main entry point for the server"""
    parser = argparse.ArgumentParser(description="Augmentorium MCP Server")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--project", help="Path to the active project")
    parser.add_argument("--port", type=int, default=6655, help="Port for the API server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--ollama-url", help="URL for the Ollama API (e.g., http://server-ip:11434)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="DEBUG", help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.info("Starting Augmentorium MCP Server")
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Update Ollama URL if specified
    if args.ollama_url:
        if 'ollama' not in config.global_config:
            config.global_config['ollama'] = {}
        config.global_config['ollama']['base_url'] = args.ollama_url
        logger.info(f"Using Ollama API at: {args.ollama_url}")
    
    # Start server
    logger.info(f"Starting server on {args.host}:{args.port}...")
    mcp_service, api_server, api_thread = start_server(config, args.port, args.project)
    
    # Keep running
    try:
        logger.info("Server started. Press Ctrl+C to stop.")
        print(f"MCP Server is running on {args.host}:{args.port}")
        print("Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        mcp_service.stop()
        logger.info("Server stopped.")

if __name__ == "__main__":
    main()