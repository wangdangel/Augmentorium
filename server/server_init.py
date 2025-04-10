"""
Server initialization for Augmentorium
"""

import os
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple

from config.manager import ConfigManager
from server.api import APIServer
from server.query import QueryProcessor, RelationshipEnricher, ContextBuilder
from utils.db_utils import VectorDB
from indexer.embedder import OllamaEmbedder

logger = logging.getLogger(__name__)

def start_api_server(
    config: ConfigManager,
    port: int = 6655,
    active_project: Optional[str] = None
) -> Tuple[APIServer, threading.Thread]:
    """
    Start the Augmentorium API server (without MCP)
    
    Args:
        config: Configuration manager
        port: Port for the API server
        active_project: Path to the active project
    
    Returns:
        Tuple[APIServer, threading.Thread]: API server and its thread
    """
    try:
        logger.info("Starting Augmentorium API server")
        
        # Get server configuration
        server_config = config.global_config.get("server", {})
        host = server_config.get("host", "localhost")
        
        # Setup active project database
        db_path = None
        if active_project:
            db_path = config.get_db_path(active_project)
        else:
            projects = config.get_all_projects()
            if projects:
                first_project = list(projects.values())[0]
                db_path = config.get_db_path(first_project)
        
        vector_db = VectorDB(db_path) if db_path else None
        
        # Initialize embedder
        ollama_config = config.global_config.get("ollama", {})
        embedder = OllamaEmbedder(
            base_url=ollama_config.get("base_url", "http://localhost:11434"),
            model=ollama_config.get("embedding_model", "codellama:34b")
        )
        
        # Initialize query processor and enrichers
        query_processor = QueryProcessor(
            vector_db=vector_db,
            expander=None,
            cache_size=config.global_config.get("server", {}).get("cache_size", 100)
        )
        relationship_enricher = RelationshipEnricher(vector_db)
        context_builder = ContextBuilder(
            max_context_size=config.global_config.get("server", {}).get("max_context_size", 8192)
        )
        
        # Create API server
        api_server = APIServer(
            config_manager=config,
            query_processor=query_processor,
            relationship_enricher=relationship_enricher,
            context_builder=context_builder,
            host=host,
            port=port
        )
        
        # Start API server in a thread
        api_thread = threading.Thread(target=api_server.run)
        api_thread.daemon = True
        api_thread.start()
        
        logger.info(f"Augmentorium API server started on {host}:{port}")
        
        return api_server, api_thread
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        raise


def main():
    """Main entry point for server"""
    from config.manager import ConfigManager
    from utils.logging import setup_logging
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
    
    # Start API server only (no MCP)
    api_server, api_thread = start_api_server(config, args.port, args.project)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Augmentorium server")
        mcp_service.stop()


if __name__ == "__main__":
    main()
