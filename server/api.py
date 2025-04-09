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
        mcp_server: MCPServer,
        host: str = "localhost",
        port: int = 6655
    ):
        """
        Initialize API server
        
        Args:
            config_manager: Configuration manager
            mcp_server: MCP server
            host: Host to bind to
            port: Port to bind to
        """
        self.config_manager = config_manager
        self.mcp_server = mcp_server
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
            """Get list of projects"""
            projects = self.config_manager.get_all_projects()
            return jsonify({"projects": projects})
        
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
            active_project = self.mcp_server.get_active_project()
            
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
            
            # Set active project
            success = self.mcp_server.set_active_project(project_path)
            
            if success:
                return jsonify({"status": "success", "message": f"Set active project: {project_path}"})
            else:
                return jsonify({"error": f"Failed to set active project: {project_path}"}), 500
        
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
            context, results = self.mcp_server.process_query(
                query=query,
                n_results=n_results,
                min_score=min_score,
                filters=filters,
                include_metadata=include_metadata
            )
            
            return jsonify({
                "context": context,
                "results": [result.to_dict() for result in results]
            })
        
        @self.app.route("/api/cache", methods=["DELETE"])
        def clear_cache() -> Response:
            """Clear query cache"""
            if self.mcp_server.query_processor:
                self.mcp_server.query_processor.clear_cache()
            
            return jsonify({"status": "success", "message": "Query cache cleared"})
    
    def run(self) -> None:
        """Run the API server"""
        self.app.run(host=self.host, port=self.port)
