from functools import wraps
from flask import jsonify, current_app, g

def require_active_project(func):
    """
    Decorator for API endpoints that require an active project.
    Returns HTTP 400 with a clear error if no active project is set.
    Assumes config_manager is available via Flask's g or current_app.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Try g first, fallback to current_app
        config_manager = getattr(g, "config_manager", None)
        if config_manager is None:
            config_manager = getattr(current_app, "config_manager", None)
        if config_manager is None:
            return (
                jsonify({
                    "error": "Server misconfiguration: config_manager not found."
                }),
                500
            )
        active_project = config_manager.get_active_project_name()
        if not active_project:
            return (
                jsonify({
                    "error": "No active project set. Please set or create a project using the /api/projects endpoint."
                }),
                400
            )
        return func(*args, **kwargs)
    return wrapper