#!/usr/bin/env python3
"""
Development script to run the Augmentorium MCP server
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path

# Add the root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from config.manager import ConfigManager
from utils.logging import setup_logging
from server.mcp import MCPServer, MCPService
from server.api import APIServer

def main():
    """Main entry point for development server"""
    parser = argparse.ArgumentParser(description="Augmentorium MCP Server (Development)")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--project", help="Path to the active project")
    parser.add_argument("--port", type=int, default=8080, help="Port for the API server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="DEBUG",
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.info("Starting Augmentorium MCP Server in development mode")
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Create MCP service
    mcp_service = MCPService(
        config_manager=config,
        active_project_path=args.project
    )
    
    # Start MCP service
    mcp_service.start()
    logger.info("MCP service started")
    
    # Create API server
    api_server = APIServer(
        config_manager=config,
        mcp_server=mcp_service.server,
        host=args.host,
        port=args.port
    )
    
    # Print listening information
    print(f"MCP Server is running.")
    print(f"API server listening on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    
    # Start API server in a thread
    import threading
    api_thread = threading.Thread(target=api_server.run)
    api_thread.daemon = True
    api_thread.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping MCP server")
        mcp_service.stop()
        logger.info("MCP server stopped")

if __name__ == "__main__":
    main()
