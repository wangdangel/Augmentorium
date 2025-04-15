from flask import Blueprint, request, jsonify, current_app, g
from server.api.project_helpers import get_project_path

chunks_bp = Blueprint('chunks', __name__, url_prefix='/api/chunks')

@chunks_bp.route('/search', methods=['POST'])
def search_chunks():
    """
    Semantic search for code chunks/passages.
    Request: { "project": str (required), "query": str, "n_results": int (optional, default 5) }
    Response: { "chunks": [ { "text": str, "file": str, "score": float, ... } ] }
    """
    data = request.json or {}
    project_name = data.get("project")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    query = data.get("query")
    n_results = data.get("n_results", 5)
    if not query:
        return jsonify({"error": "Missing query"}), 400

    config_manager = getattr(g, "config_manager", None)
    if config_manager is None:
        config_manager = getattr(current_app, "config_manager", None)
    if config_manager is None:
        return jsonify({"error": "No config manager found"}), 500

    project_path = get_project_path(config_manager, project_name)
    if not project_path:
        return jsonify({"error": "Project not found"}), 404

    # Use the actual query_processor logic, routed by project
    query_processor = getattr(current_app, "query_processor", None)
    if not query_processor:
        return jsonify({"error": "Server internal error: QueryProcessor not initialized"}), 500

    # If your query_processor is project-specific, replace this with a lookup by project_name
    results = query_processor.query(
        query_text=query,
        n_results=n_results
    )

    # Assume results is a list of objects with .to_dict() or similar
    return jsonify({"chunks": [r.to_dict() for r in results]})
