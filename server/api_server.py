"""
API server for Augmentorium
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
# Import Blueprints
from server.api.api_projects import projects_bp, init_projects_blueprint
from server.api.api_documents import documents_bp
from server.api.api_query import query_bp
from server.api.api_graph import graph_bp
from server.api.api_cache import cache_bp
from server.api.api_health import health_bp
from server.api.api_indexer import indexer_bp
from server.api.api_files import files_bp
from server.api.api_chunks import chunks_bp
from server.api.api_explain import explain_bp
from server.api.api_graph_neighbors import graph_neighbors_bp
from server.api.api_stats import stats_bp
from server.api.api_health_llm_window import health_llm_window_bp
from server.api.api_query_mcp import query_mcp_bp

from config.manager import ConfigManager

logger = logging.getLogger(__name__)

from functools import wraps

class APIServer:
    """API server for Augmentorium management"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        indexer_status,
        host: str = "localhost",
        port: int = 6655,
        query_processors=None,
        relationship_enrichers=None,
        context_builders=None
    ):
        """
        Initialize API server
        
        Args:
            config_manager: Configuration manager
            host: Host to bind to
            port: Port to bind to
            query_processors: Dict of project_name -> QueryProcessor
            relationship_enrichers: Dict of project_name -> RelationshipEnricher
            context_builders: Dict of project_name -> ContextBuilder
        """
        import threading
        self.config_manager = config_manager
        self.host = host
        self.port = port
        self.indexer_status = indexer_status
        self._project_lock = threading.Lock()
        self.query_processors = query_processors or {}
        self.relationship_enrichers = relationship_enrichers or {}
        self.context_builders = context_builders or {}
        self.app = Flask("augmentorium")
        CORS(self.app, origins=["http://localhost:5173"])  # Allow frontend dev server
        self.app.config_manager = config_manager
        
        # Set up routes
        # Register Blueprints

        # Ensure both blueprints share the same status object
        from server.api.api_indexer import init_indexer_blueprint
        init_indexer_blueprint(self.indexer_status)
        from server.api.api_projects import init_projects_blueprint
        init_projects_blueprint(self.config_manager, self.indexer_status)
        self.app.register_blueprint(projects_bp)
        self.app.register_blueprint(documents_bp)
        self.app.register_blueprint(query_bp)
        self.app.register_blueprint(graph_bp)
        self.app.register_blueprint(cache_bp)
        self.app.register_blueprint(health_bp)
        self.app.register_blueprint(indexer_bp)
        self.app.register_blueprint(files_bp)
        self.app.register_blueprint(chunks_bp)
        self.app.register_blueprint(explain_bp)
        self.app.register_blueprint(graph_neighbors_bp)
        self.app.register_blueprint(stats_bp)
        self.app.register_blueprint(health_llm_window_bp)
        self.app.register_blueprint(query_mcp_bp)
        
        logger.info(f"Initialized API server on {host}:{port}")

    def reload_project_components(self, project_name):
        """
        Reload project-specific components (QueryProcessor, VectorDB, etc.) for the given project.
        """
        import threading
        from utils.project_db_mapping import build_project_db_mapping, get_db_paths_for_project
        from indexer.embedder import OllamaEmbedder
        from server.query import QueryExpander, QueryProcessor, RelationshipEnricher, ContextBuilder
        from utils.db_utils import VectorDB

        with self._project_lock:
            logger.info(f"Reloading project-specific components for project {project_name}...")
            # Rebuild mapping and get new db paths
            project_db_mapping = build_project_db_mapping(self.config_manager)
            db_paths = get_db_paths_for_project(project_db_mapping, project_name)
            if not db_paths:
                logger.error(f"No valid project database paths found for project {project_name} during reload.")
                raise RuntimeError(f"No valid project database paths found for project {project_name} during reload.")
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
                graph_db_path=graph_db_path
            )
            relationship_enricher = RelationshipEnricher(vector_db)
            context_builder = ContextBuilder(
                max_context_size=self.config_manager.config.get("chunking", {}).get("max_chunk_size", 1024)
            )
            # Attach new components directly to app
            self.app.query_processor = query_processor
            self.app.relationship_enricher = relationship_enricher
            self.app.context_builder = context_builder
            logger.info(f"Project-specific components reloaded and updated in app successfully for project {project_name}.")

    def run(self) -> None:
        """Run the API server"""
        self.app.run(host=self.host, port=self.port)
