"""
Server initialization for Augmentorium
"""

import os
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple

from config.manager import ConfigManager
from server.api_server import APIServer
from server.query import QueryProcessor, RelationshipEnricher, ContextBuilder, QueryExpander
from utils.db_utils import VectorDB
from indexer.embedder import OllamaEmbedder
from utils.project_db_mapping import build_project_db_mapping, get_db_paths_for_project

logger = logging.getLogger(__name__)

def start_api_server(
    config: ConfigManager,
    port: int = 6655,
) -> Tuple[APIServer, threading.Thread]:
    """
    Start the Augmentorium API server (without MCP)
    
    Args:
        config: Configuration manager
        port: Port for the API server
    
    Returns:
        Tuple[APIServer, threading.Thread]: API server and its thread
    """
    try:
        logger.info("Starting Augmentorium API server")
        
        # Get server configuration
        server_config = config.config.get("server", {})
        host = server_config.get("host", "localhost")

        # Build mapping for all projects
        project_db_mapping = build_project_db_mapping(config)
        project_paths = config.config.get("projects", {})

        # Use the FIRST project as the default (for now)
        # Or, optionally, you could use a specific project or make this configurable
        first_project = next(iter(project_paths.items()), None)
        if not first_project:
            raise RuntimeError("No projects found in config.")
        project_name, project_path = first_project
        db_paths = get_db_paths_for_project(project_db_mapping, project_path)
        if not db_paths:
            logger.warning(f"No DB paths found for project: {project_path}")
            raise RuntimeError(f"No DB paths found for project: {project_path}")

        # Initialize embedder (not project-dependent, always available)
        ollama_config = config.config.get("ollama", {})
        embedder = OllamaEmbedder(
            base_url=ollama_config.get("base_url"),
            model=ollama_config.get("embedding_model")
        )

        # Initialize single query processor and enrichers
        query_expander = QueryExpander(ollama_embedder=embedder)
        query_processor = QueryProcessor(
            vector_db=VectorDB(db_paths["chroma_db"]),
            expander=query_expander,
            cache_size=server_config.get("cache_size", 100),
            graph_db_path=db_paths["code_graph_db"]
        )
        relationship_enricher = RelationshipEnricher(VectorDB(db_paths["chroma_db"]))
        context_builder = ContextBuilder(
            max_context_size=config.config.get("chunking", {}).get("max_chunk_size", 1024)
        )

        # Create shared indexer status object
        indexer_status = {}

        # Create API server WITHOUT MCPServer reference
        api_server = APIServer(
            config_manager=config,
            indexer_status=indexer_status,
            host=host,
            port=port,
            query_processors=None,  # Not used anymore
            relationship_enrichers=None,
            context_builders=None
        )

        # Attach singletons to app (for use in endpoints)
        api_server.app.query_processor = query_processor
        api_server.app.relationship_enricher = relationship_enricher
        api_server.app.context_builder = context_builder

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
    api_server, api_thread = start_api_server(config, args.port)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Augmentorium server")


if __name__ == "__main__":
    main()
