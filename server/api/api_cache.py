from flask import Blueprint, jsonify, current_app
from server.api.common import require_active_project

cache_bp = Blueprint('cache', __name__, url_prefix='/api/cache')

@cache_bp.route('/', methods=['GET'])
def cache_placeholder():
    return jsonify({"status": "ok"})

@cache_bp.route('/', methods=['DELETE'])
@require_active_project
def clear_cache():
    """
    Clear query cache.

    Error Response (if no active project):
        HTTP 400
        {
            "error": "No active project set. Please set or create a project using the /api/projects endpoint."
        }
    """
    current_app.query_processor.clear_cache()
    return jsonify({"status": "success", "message": "Query cache cleared"})