"""
API server for Augmentorium
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from flask import Flask, request, jsonify, Response
# Import Blueprints
from server.api.api_projects import projects_bp, init_projects_blueprint
from server.api.api_documents import documents_bp
from server.api.api_query import query_bp
from server.api.api_graph import graph_bp
from server.api.api_cache import cache_bp
from server.api.api_health import health_bp
from server.api.api_indexer import indexer_bp

from config.manager import ConfigManager
from server.mcp import MCPServer

logger = logging.getLogger(__name__)

from functools import wraps

def require_active_project(func):
    """
    Decorator for API endpoints that require an active project.
    Returns HTTP 400 with a clear error if no active project is set.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        active_project = self.config_manager.get_active_project_name()
        if not active_project:
            return (
                jsonify({
                    "error": "No active project set. Please set or create a project using the /api/projects endpoint."
                }),
                400
            )
        return func(self, *args, **kwargs)
    return wrapper

class APIServer:
    """API server for Augmentorium management"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        query_processor,
        relationship_enricher,
        context_builder,
        indexer_status,
        host: str = "localhost",
        port: int = 6655
    ):
        """
        Initialize API server
        
        Args:
            config_manager: Configuration manager
            query_processor: QueryProcessor instance
            relationship_enricher: RelationshipEnricher instance
            context_builder: ContextBuilder instance
            host: Host to bind to
            port: Port to bind to
        """
        import threading
        self.config_manager = config_manager
        self.query_processor = query_processor
        self.relationship_enricher = relationship_enricher
        self.context_builder = context_builder
        self.host = host
        self.port = port

        self.indexer_status = indexer_status

        # Lock for project component reloads and query safety
        self._project_lock = threading.Lock()
        
        # Initialize Flask app
        self.app = Flask("augmentorium")
        self.app.config_manager = config_manager
        self.app.query_processor = query_processor
        self.app.relationship_enricher = relationship_enricher
        self.app.context_builder = context_builder
        
        # Set up routes
        # Register Blueprints

        # Ensure both blueprints share the same status object
        from server.api.api_indexer import init_indexer_blueprint
        init_indexer_blueprint(self.indexer_status)
        init_projects_blueprint(self.config_manager, self.indexer_status)
        self.app.register_blueprint(projects_bp)
        self.app.register_blueprint(documents_bp)
        self.app.register_blueprint(query_bp)
        self.app.register_blueprint(graph_bp)
        self.app.register_blueprint(cache_bp)
        self.app.register_blueprint(health_bp)
        self.app.register_blueprint(indexer_bp)
        
        logger.info(f"Initialized API server on {host}:{port}")

    def reload_project_components(self):
        """
        Reload project-specific components (QueryProcessor, VectorDB, etc.) for the new active project.
        """
        import threading
        from utils.project_db_mapping import build_project_db_mapping, get_db_paths_for_project
        from indexer.embedder import OllamaEmbedder
        from server.query import QueryExpander, QueryProcessor, RelationshipEnricher, ContextBuilder
        from utils.db_utils import VectorDB

        with self._project_lock:
            logger.info("Reloading project-specific components for new active project...")
            # Rebuild mapping and get new db paths
            project_db_mapping = build_project_db_mapping(self.config_manager)
            active_project_name = self.config_manager.get_active_project_name()
            db_paths = get_db_paths_for_project(project_db_mapping, active_project_name)
            if not db_paths:
                logger.error("No valid project database paths found for the active project during reload.")
                raise RuntimeError("No valid project database paths found for the active project during reload.")
            vector_db = VectorDB(db_paths["chroma_db"])
            ollama_config = self.config_manager.config.get("ollama", {})
            embedder = OllamaEmbedder(
                base_url=ollama_config.get("base_url"),
                model=ollama_config.get("embedding_model")
            )
            query_expander = QueryExpander(ollama_embedder=embedder)
            graph_db_path = db_paths["code_graph_db"]
            server_config = self.config_manager.config.get("server", {})
            query_processor = QueryProcessor(
                vector_db=vector_db,
                expander=query_expander,
                cache_size=server_config.get("cache_size", 100),
                graph_db_path=graph_db_path,
                project_db_mapping=project_db_mapping
            )
            relationship_enricher = RelationshipEnricher(vector_db)
            context_builder = ContextBuilder(
                max_context_size=self.config_manager.config.get("chunking", {}).get("max_chunk_size", 1024)
            )
            self.query_processor = query_processor
            self.relationship_enricher = relationship_enricher
            self.context_builder = context_builder
            logger.info("Project-specific components reloaded successfully.")
    
    def run(self) -> None:
        """Run the API server"""
        self.app.run(host=self.host, port=self.port)
