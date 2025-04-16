from flask import Blueprint, jsonify, current_app, g, request
import os
import yaml
from server.api.project_helpers import get_project_path
from pathspec import PathSpec

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

# Helper to load ignore patterns from config.yaml and compile with pathspec

def load_ignore_spec():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        patterns = config.get('indexer', {}).get('ignore_patterns', [])
        spec = PathSpec.from_lines('gitwildmatch', patterns)
        return spec
    except Exception as e:
        print(f"[WARN] Could not load ignore patterns from config.yaml: {e}")
        return PathSpec.from_lines('gitwildmatch', [])

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
    ignore_spec = load_ignore_spec()
    for root, dirs, files in os.walk(project_path):
        rel_root = os.path.relpath(root, project_path)
        # Skip ignored directories in-place
        dirs[:] = [d for d in dirs if not ignore_spec.match_file(os.path.join(rel_root, d))]
        for name in files:
            rel_path = os.path.normpath(os.path.join(rel_root, name))
            if ignore_spec.match_file(rel_path):
                continue
            file_path = os.path.join(root, name)
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
