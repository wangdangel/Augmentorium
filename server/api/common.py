from functools import wraps
from flask import jsonify, current_app, g

# Removed require_active_project decorator; all projects are always available