from flask import Blueprint, jsonify, current_app, g, request
import os
from server.api.project_helpers import get_project_path

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

@files_bp.route('/', methods=['GET'])
def list_files():
    """
    List all indexed files in the specified project with metadata.
    Query params:
      - project: str, required
      - max_files: int, optional, limit number of files returned (default 20)
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
    if not project_path or not os.path.isdir(project_path):
        return jsonify({"error": "Project path not found"}), 400

    max_files = request.args.get("max_files", default=20, type=int)
    file_list = []
    for root, dirs, files in os.walk(project_path):
        for name in files:
            file_path = os.path.join(root, name)
            rel_path = os.path.relpath(file_path, project_path)
            try:
                stat = os.stat(file_path)
                file_list.append({
                    "name": name,
                    "relative_path": rel_path,
                    "absolute_path": file_path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
            except Exception as e:
                file_list.append({
                    "name": name,
                    "relative_path": rel_path,
                    "absolute_path": file_path,
                    "error": str(e)
                })
    total_files = len(file_list)
    truncated = False
    if total_files > max_files:
        file_list = file_list[:max_files]
        truncated = True
    resp = {"files": file_list, "total_files": total_files}
    if truncated:
        resp["warning"] = f"Result truncated to {max_files} files. Use filters or increase max_files if needed."
    return jsonify(resp)
