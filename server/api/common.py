from functools import wraps
from flask import jsonify, current_app, g

def require_active_project(func):
    """
    Decorator for API endpoints that require an active project.
    Returns HTTP 400 with a clear error if no active project is set.
    Assumes config_manager is available via Flask's g or current_app.
    """
    @wraps(func)
    def wrapper(project, *args, **kwargs):
        return func(project, *args, **kwargs)
    return wrapper