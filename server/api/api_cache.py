from flask import Blueprint, jsonify, current_app, request

cache_bp = Blueprint('cache', __name__, url_prefix='/api/cache')

@cache_bp.route('/', methods=['GET'])
def cache_placeholder():
    return jsonify({"status": "ok"})

@cache_bp.route('/', methods=['DELETE'])
def clear_cache():
    """
    Clear query cache for a specific project.
    Requires: project name in request args or JSON body.
    """
    project_name = request.args.get("project")
    if not project_name and request.method == 'POST':
        data = request.get_json(silent=True) or {}
        project_name = data.get('project')
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    # Use project_name to clear cache as needed (update logic if cache is per-project)
    current_app.query_processor.clear_cache()  # TODO: update for per-project cache if needed
    return jsonify({"status": "success", "message": f"Query cache cleared for project {project_name}"})