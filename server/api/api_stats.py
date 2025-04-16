from flask import Blueprint, jsonify, current_app, g, request
from server.api.project_helpers import get_project_path

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@stats_bp.route('/', methods=['GET'])
def get_stats():
    """
    Return stats on number of indexed files, chunks, queries served, etc. for a project.
    Query params:
      - project: str, required
    """
    project_name = request.args.get("project")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400

    config_manager = getattr(g, "config_manager", None)
    if config_manager is None:
        config_manager = getattr(current_app, "config_manager", None)
    if config_manager is None:
        return jsonify({"error": "No config manager found"}), 500

    project_path = get_project_path(config_manager, project_name)
    if not project_path:
        return jsonify({"error": "Project not found"}), 404

    # Example: Use your backend logic to get stats for this project
    # Replace with real logic as needed
    stats = {}
    # Example: count files
    import os
    file_count = 0
    for root, dirs, files in os.walk(project_path):
        file_count += len(files)
    stats["files_indexed"] = file_count
    # TODO: Add chunk and query stats per project if available
    stats["chunks_indexed"] = None
    stats["queries_served"] = None
    stats["project"] = project_name
    return jsonify(stats)
