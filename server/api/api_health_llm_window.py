from flask import Blueprint, jsonify, request, g, current_app
from server.api.project_helpers import get_project_path

health_llm_window_bp = Blueprint('health_llm_window', __name__, url_prefix='/api/health/llm_window')

@health_llm_window_bp.route('/', methods=['GET'])
def get_llm_window():
    """
    Returns a recommended max token/file count for LLM requests, based on config and project.
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

    # Example: Use your backend logic to determine LLM window for this project
    # Replace with real logic as needed
    # For now, just return defaults
    return jsonify({"max_files": 20, "max_tokens": 16000, "project": project_name})
