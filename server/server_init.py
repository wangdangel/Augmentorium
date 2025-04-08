"""
Server initialization for Augmentorium
"""

import os
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple

from augmentorium.config.manager import ConfigManager
from augmentorium.server.mcp import MCPServer, MCPService
from augmentorium.server.api import APIServer

logger = logging.getLogger(__name__)

def start_server(
    config: ConfigManager,
    port: int = 6655,
    active_project: Optional[str] = None
) -> Tuple[MCPService, APIServer, threading.Thread]:
    """
    Start the Augmentorium server
    
    Args:
        config: Configuration manager
        port: Port for the API server
        active_project: Path to the active project
    
    Returns:
        Tuple[MCPService, APIServer, threading.Thread]: Server components
    """
    try:
        logger.info("Starting Augmentorium server")
        
        # Get server configuration
        server_config = config.global_config.get("server", {})
        host = server_config.get("host", "localhost")
        
        # Create and start MCP service
        mcp_service = MCPService(
            config_manager=config,
            active_project_path=active_project
        )
        mcp_service.start()
        
        # Create API server
        api_server = APIServer(
            config_manager=config,
            mcp_server=mcp_service.server,
            host=host,
            port=port
        )
        
        # Start API server in a thread
        api_thread = threading.Thread(target=api_server.run)
        api_thread.daemon = True
        api_thread.start()
        
        logger.info(f"Augmentorium server started on {host}:{port}")
        
        return mcp_service, api_server, api_thread
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


def main():
    """Main entry point for server"""
    from augmentorium.config.manager import ConfigManager
    from augmentorium.utils.logging import setup_logging
    import argparse
    import time
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Augmentorium Server")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--project", help="Path to the active project")
    parser.add_argument("--port", type=int, default=6655, help="Port for the API server")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Start server
    mcp_service, api_server, api_thread = start_server(config, args.port, args.project)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Augmentorium server")
        mcp_service.stop()


if __name__ == "__main__":
    main()
