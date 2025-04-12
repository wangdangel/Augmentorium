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
        
        # Global variable to store latest indexer status
        self.indexer_status = {}

        @self.app.route("/api/indexer_status", methods=["POST"])
        def update_indexer_status() -> Response:
            """Receive status update from indexer"""
            try:
                data = request.json
                if not data or "projects" not in data:
                    return jsonify({"error": "Invalid status update"}), 400
                self.indexer_status = data
                return jsonify({"status": "success"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

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

            # print("DEBUG: self.config_manager.global_config =", self.config_manager.config) # DEBUG: Changed to self.config if needed
            projects_dict = self.config_manager.get_all_projects()
            # print("DEBUG: projects_dict =", projects_dict) # DEBUG
            projects_list = []

            # Build a lookup from indexer status
            indexer_status_map = {}
            try:
                for p in self.indexer_status.get("projects", []):
                    indexer_status_map[p.get("path")] = p
            except Exception:
                pass

            if not projects_dict:
                projects_dict = {}
            for name, path in projects_dict.items():
                size = 0
                try:
                    size = get_dir_size(path)
                except Exception:
                    pass

                status_info = indexer_status_map.get(path, {})

                project_info = {
                    "name": name,
                    "path": path,
                    "status": status_info.get("status", "idle"),
                    "size": status_info.get("size", size),
                    "lastIndexed": status_info.get("lastIndexed"),
                    "error": status_info.get("error")
                }
                projects_list.append(project_info)

            print("DEBUG: projects_list =", projects_list)
            return jsonify({"projects": projects_list})
        
        @self.app.route("/api/projects", methods=["POST"])
        def add_project() -> Response:
            """Add a project"""
            data = request.json
            
            if not data or "path" not in data:
                return jsonify({"error": "Missing project path"}), 400
            
            project_path = data["path"]
            project_name = data.get("name")

            # Sanitize project_path: trim and remove surrounding quotes
            cleaned_path = project_path.strip().strip('"').strip("'")

            # Reject if suspicious or empty
            if not cleaned_path or '"' in cleaned_path or "'" in cleaned_path:
                return jsonify({"error": "Invalid project path format"}), 400

            # Use ConfigManager to initialize the project.
            # This handles directory creation, config file setup, and adding to global registry.
            try:
                # Check if path is already registered to provide a more specific message
                existing_projects = self.config_manager.get_all_projects()
                # Safeguard against get_all_projects returning None unexpectedly
                if existing_projects is None:
                    logger.warning("ConfigManager.get_all_projects() returned None, treating as empty.")
                    existing_projects = {}

                if cleaned_path in existing_projects.values():
                    # Find the name associated with this path
                    existing_name = next((name for name, path in existing_projects.items() if path == cleaned_path), None)
                    message = f"Project path '{cleaned_path}' is already registered as '{existing_name}'."
                    # Optionally, update the name if a new one was provided? For now, just report.
                    # if project_name and project_name != existing_name:
                    #     # Handle name update logic if desired
                    #     pass
                    return jsonify({"status": "success", "message": message})

                # If not registered, initialize it
                success = self.config_manager.initialize_project(cleaned_path, project_name)

                if success:
                    # Get the final name assigned by initialize_project
                    final_name = project_name or os.path.basename(cleaned_path) # Initial guess
                    # Reload projects to get the potentially suffixed name
                    updated_projects = self.config_manager.get_all_projects()
                    # Safeguard against None again
                    if updated_projects is None:
                        logger.warning("ConfigManager.get_all_projects() returned None after initialization, treating as empty.")
                        updated_projects = {}
                    
                    # Find the final name, using the initial guess as fallback
                    final_name = next((name for name, path in updated_projects.items() if path == os.path.abspath(cleaned_path)), final_name)

                    return jsonify({
                        "status": "success",
                        "message": f"Project '{final_name}' initialized successfully at '{cleaned_path}'."
                    })
                else:
                    # initialize_project logs errors, return a generic failure message
                    return jsonify({"status": "error", "message": f"Failed to initialize project at '{cleaned_path}'."}), 500

            except FileNotFoundError:
                 return jsonify({"status": "error", "message": f"Project path '{cleaned_path}' does not exist or is not accessible."}), 400
            except Exception as e:
                logger.error(f"Error during project initialization for path '{cleaned_path}': {e}", exc_info=True)
                return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500
        
        @self.app.route("/api/projects/<name>", methods=["DELETE"])
        def remove_project(name: str) -> Response:
            """Remove a project"""
            # Remove project
            success = self.config_manager.remove_project(name)
            
            if success:
                return jsonify({"status": "success", "message": f"Removed project: {name}"})
            else:
                return jsonify({"error": f"Failed to remove project: {name}"}), 404

        @self.app.route("/api/projects/<project_name>/reindex", methods=["POST"])
        def reindex_project(project_name: str) -> Response:
            """Trigger reindexing for a specific project"""
            # TODO: Implement actual reindex logic here
            return jsonify({"status": "success", "message": f"Reindex triggered for project {project_name}"}), 200
        
        @self.app.route("/api/projects/active", methods=["GET"])
        def get_active_project() -> Response:
            """Get active project"""
            active_name = self.config_manager.get_active_project_name()
            projects = self.config_manager.get_all_projects()
            if active_name and active_name in projects:
                return jsonify({
                    "project": {
                        "name": active_name,
                        "path": projects[active_name]
                    }
                })
            else:
                return jsonify({"project": None})

        @self.app.route("/api/projects/active", methods=["POST"])
        def set_active_project() -> Response:
            """Set active project"""
            data = request.json

            if not data or "name" not in data:
                return jsonify({"error": "Missing project name"}), 400

            project_name = data["name"]
            projects = self.config_manager.get_all_projects()
            if project_name not in projects:
                return jsonify({"error": "Project not found"}), 404

            self.config_manager.set_active_project_name(project_name)
            return jsonify({"status": "success", "message": f"Set active project: {project_name}"})
        
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
            """Trigger reindexing of all documents in the active project"""
            active_project_name = self.config_manager.get_active_project_name()
            if not active_project_name:
                return jsonify({"error": "No active project set"}), 400
            
            project_path = self.config_manager.get_project_path(active_project_name)
            if not project_path:
                return jsonify({"error": "Active project not found"}), 404
            
            metadata_dir = self.config_manager.get_metadata_path(project_path)
            hash_cache_file = os.path.join(metadata_dir, "hash_cache.json")
            
            try:
                if os.path.exists(hash_cache_file):
                    os.remove(hash_cache_file)
                return jsonify({"status": "success", "message": f"Reindex triggered for project {active_project_name}"})
            except Exception as e:
                logger.error(f"Error triggering reindex for project {active_project_name}: {e}")
                return jsonify({"error": f"Failed to trigger reindex: {e}"}), 500

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
