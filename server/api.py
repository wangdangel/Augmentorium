"""
API server for Augmentorium
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from flask import Flask, request, jsonify, Response

from config.manager import ConfigManager
from server.mcp import MCPServer

logger = logging.getLogger(__name__)

class APIServer:
    """API server for Augmentorium management"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        query_processor,
        relationship_enricher,
        context_builder,
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
        self.config_manager = config_manager
        self.query_processor = query_processor
        self.relationship_enricher = relationship_enricher
        self.context_builder = context_builder
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask("augmentorium")
        
        # Set up routes
        self._setup_routes()
        
        logger.info(f"Initialized API server on {host}:{port}")
    
    def _setup_routes(self) -> None:
        """Set up API routes"""
        
        @self.app.route("/api/health", methods=["GET"])
        def health() -> Response:
            """Health check endpoint"""
            return jsonify({"status": "ok"})
        
        @self.app.route("/api/projects", methods=["GET"])
        def get_projects() -> Response:
            """Get list of projects with metadata"""
            import time

            def get_dir_size(path):
                total = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        try:
                            total += os.path.getsize(fp)
                        except Exception:
                            pass
                return total

            projects_dict = self.config_manager.get_all_projects()
            projects_list = []
            for name, path in projects_dict.items():
                size = 0
                try:
                    size = get_dir_size(path)
                except Exception:
                    pass

                # TODO: Replace with real status and lastIndexed
                project_info = {
                    "name": name,
                    "path": path,
                    "status": "idle",
                    "size": size,
                    "lastIndexed": None
                }
                projects_list.append(project_info)

            return jsonify({"projects": projects_list})
        
        @self.app.route("/api/projects", methods=["POST"])
        def add_project() -> Response:
            """Add a project"""
            data = request.json
            
            if not data or "path" not in data:
                return jsonify({"error": "Missing project path"}), 400
            
            project_path = data["path"]
            project_name = data.get("name")
            
            # Add project
            success = self.config_manager.add_project(project_path, project_name)
            
            if success:
                return jsonify({"status": "success", "message": f"Added project: {project_path}"})
            else:
                return jsonify({"error": f"Failed to add project: {project_path}"}), 500
        
        @self.app.route("/api/projects/<name>", methods=["DELETE"])
        def remove_project(name: str) -> Response:
            """Remove a project"""
            # Remove project
            success = self.config_manager.remove_project(name)
            
            if success:
                return jsonify({"status": "success", "message": f"Removed project: {name}"})
            else:
                return jsonify({"error": f"Failed to remove project: {name}"}), 404
        
        @self.app.route("/api/projects/active", methods=["GET"])
        def get_active_project() -> Response:
            """Get active project"""
            # For now, just return the first project as active
            projects = self.config_manager.get_all_projects()
            active_project = None
            if projects:
                active_project = list(projects.values())[0]
            
            if active_project:
                return jsonify({"project_path": active_project})
            else:
                return jsonify({"error": "No active project"}), 404
        
        @self.app.route("/api/projects/active", methods=["POST"])
        def set_active_project() -> Response:
            """Set active project"""
            data = request.json
            
            if not data or "path" not in data:
                return jsonify({"error": "Missing project path"}), 400
            
            project_path = data["path"]
            
            # For now, just acknowledge the request (no persistent active project state)
            return jsonify({"status": "success", "message": f"Set active project: {project_path}"})
        
        @self.app.route("/api/query", methods=["POST"])
        def process_query() -> Response:
            """Process a query"""
            data = request.json
            
            if not data or "query" not in data:
                return jsonify({"error": "Missing query"}), 400
            
            query = data["query"]
            n_results = data.get("n_results", 10)
            min_score = data.get("min_score", 0.0)
            filters = data.get("filters")
            include_metadata = data.get("include_metadata", True)
            
            # Process query
            results = self.query_processor.query(
                query_text=query,
                n_results=n_results,
                min_score=min_score,
                filters=filters
            )
            
            # Enrich results
            results = self.relationship_enricher.enrich_results(results)
            
            # Build context
            context = self.context_builder.build_context(
                query=query,
                results=results,
                include_metadata=include_metadata
            )
            
            return jsonify({
                "context": context,
                "results": [result.to_dict() for result in results]
            })
        
        @self.app.route("/api/cache", methods=["DELETE"])
        def clear_cache() -> Response:
            """Clear query cache"""
            self.query_processor.clear_cache()
            return jsonify({"status": "success", "message": "Query cache cleared"})

        @self.app.route("/api/documents", methods=["GET"])
        def list_documents() -> Response:
            """List indexed documents"""
            # TODO: Replace with real document metadata retrieval
            docs = [
                {
                    "id": "doc1",
                    "name": "example.py",
                    "size": 12345,
                    "uploaded_at": "2024-01-01T12:00:00Z",
                    "status": "indexed",
                    "chunkCount": 10,
                    "lastIndexed": "2024-01-01T12:05:00Z"
                }
            ]
            return jsonify({"documents": docs})

        @self.app.route("/api/documents/upload", methods=["POST"])
        def upload_document() -> Response:
            """Upload a new document"""
            # TODO: Implement file upload handling
            return jsonify({"status": "success", "message": "Upload endpoint not yet implemented"}), 501

        @self.app.route("/api/documents/reindex", methods=["POST"])
        def reindex_all_documents() -> Response:
            """Trigger reindexing of all documents"""
            # TODO: Implement reindexing logic
            return jsonify({"status": "success", "message": "Reindex all not yet implemented"}), 501

        @self.app.route("/api/documents/<doc_id>/reindex", methods=["POST"])
        def reindex_document(doc_id: str) -> Response:
            """Trigger reindexing of a specific document"""
            # TODO: Implement per-document reindexing
            return jsonify({"status": "success", "message": f"Reindex {doc_id} not yet implemented"}), 501

        @self.app.route("/api/graph", methods=["GET"])
        def get_graph() -> Response:
            """Return code relationship graph data"""
            # TODO: Replace with real graph data
            graph = {
                "nodes": [
                    {"id": "file1.py", "group": "file"},
                    {"id": "file2.py", "group": "file"},
                    {"id": "ClassA", "group": "class"},
                    {"id": "func_a", "group": "function"},
                    {"id": "func_b", "group": "function"},
                ],
                "links": [
                    {"source": "file1.py", "target": "ClassA"},
                    {"source": "ClassA", "target": "func_a"},
                    {"source": "file2.py", "target": "func_b"},
                    {"source": "func_a", "target": "func_b"},
                ],
            }
            return jsonify(graph)
    
    def run(self) -> None:
        """Run the API server"""
        self.app.run(host=self.host, port=self.port)
