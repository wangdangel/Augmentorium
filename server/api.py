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

            print("DEBUG: self.config_manager.global_config =", self.config_manager.global_config)
            projects_dict = self.config_manager.get_all_projects()
            print("DEBUG: projects_dict =", projects_dict)
            projects_list = []

            # Build a lookup from indexer status
            indexer_status_map = {}
            try:
                for p in self.indexer_status.get("projects", []):
                    indexer_status_map[p.get("path")] = p
            except Exception:
                pass

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

            # Reject if suspicious
            if not cleaned_path or '"' in cleaned_path or "'" in cleaned_path:
                return jsonify({"error": "Invalid project path"}), 400

            # Initialize or add project
            if not os.path.exists(cleaned_path):
                success = self.config_manager.initialize_project(cleaned_path, project_name)
            else:
                # Always append to project registry
                try:
                    projects = self.config_manager.get_all_projects()
                    # Avoid duplicates
                    if cleaned_path not in projects.values():
                        # Use provided name or folder name
                        base_name = project_name or os.path.basename(cleaned_path)
                        name_to_use = base_name
                        suffix = 1
                        # Ensure unique name
                        while name_to_use in projects and projects[name_to_use] != cleaned_path:
                            name_to_use = f"{base_name}_{suffix}"
                            suffix += 1
                        projects[name_to_use] = cleaned_path
                        self.config_manager.global_config["projects"] = projects
                        self.config_manager._save_global_config()
                    success = True
                except Exception:
                    success = False

            response = {
                "status": "success" if success else "error",
                "message": "",
                "details": {
                    "project_initialized": success,
                    "graph_db_initialized": False,
                    "warnings": [],
                    "errors": []
                }
            }

            if not success:
                response["status"] = "error"
                response["message"] = f"Failed to add project: {cleaned_path}"
                return jsonify(response), 500

            # Initialize graph database and required folders
            try:
                from utils.graph_db import initialize_graph_db
                import os as _os

                augmentorium_dir = _os.path.join(cleaned_path, ".Augmentorium")
                _os.makedirs(augmentorium_dir, exist_ok=True)

                # Graph DB
                graph_db_path = _os.path.join(augmentorium_dir, "code_graph.db")
                initialize_graph_db(graph_db_path)
                response["details"]["graph_db_initialized"] = True

                # Vector DB folder
                chroma_dir = _os.path.join(augmentorium_dir, "chroma")
                try:
                    _os.makedirs(chroma_dir, exist_ok=True)
                    response["details"]["chroma_dir_created"] = True
                except Exception as e:
                    response["details"]["chroma_dir_created"] = False
                    response["details"]["warnings"].append(f"Failed to create chroma dir: {e}")

                # Cache folder
                cache_dir = _os.path.join(augmentorium_dir, "cache")
                try:
                    _os.makedirs(cache_dir, exist_ok=True)
                    response["details"]["cache_dir_created"] = True
                except Exception as e:
                    response["details"]["cache_dir_created"] = False
                    response["details"]["warnings"].append(f"Failed to create cache dir: {e}")

                # Metadata folder
                metadata_dir = _os.path.join(augmentorium_dir, "metadata")
                try:
                    _os.makedirs(metadata_dir, exist_ok=True)
                    response["details"]["metadata_dir_created"] = True
                except Exception as e:
                    response["details"]["metadata_dir_created"] = False
                    response["details"]["warnings"].append(f"Failed to create metadata dir: {e}")

                # Chroma DB folder
                chroma_db_dir = _os.path.join(augmentorium_dir, "chroma_db")
                try:
                    _os.makedirs(chroma_db_dir, exist_ok=True)
                    response["details"]["chroma_db_dir_created"] = True
                except Exception as e:
                    response["details"]["chroma_db_dir_created"] = False
                    response["details"]["warnings"].append(f"Failed to create chroma_db dir: {e}")

                # Config YAML
                config_yaml_path = _os.path.join(augmentorium_dir, "config.yaml")
                try:
                    import yaml as _yaml
                    config_data = None
                    if not _os.path.exists(config_yaml_path):
                        from config.defaults import DEFAULT_PROJECT_CONFIG
                        config_data = DEFAULT_PROJECT_CONFIG.copy()
                        response["details"]["config_yaml_created"] = True
                    else:
                        with open(config_yaml_path, "r") as f:
                            config_data = _yaml.safe_load(f) or {}
                        response["details"]["config_yaml_created"] = False

                    # Set project name if provided
                    if project_name:
                        if "project" not in config_data:
                            config_data["project"] = {}
                        config_data["project"]["name"] = project_name

                    with open(config_yaml_path, "w") as f:
                        _yaml.dump(config_data, f, default_flow_style=False)

                except Exception as e:
                    response["details"].setdefault("warnings", []).append(f"Failed to create/update config.yaml: {e}")

                response["message"] = f"Project fully initialized at {cleaned_path}"
                return jsonify(response)
            except Exception as e:
                response["status"] = "error"
                response["message"] = f"Project created but failed to initialize graph DB or folders: {e}"
                response["details"]["errors"].append(str(e))
                return jsonify(response), 500
        
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
