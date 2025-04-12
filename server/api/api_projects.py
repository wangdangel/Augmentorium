from flask import Blueprint, jsonify, request
import os

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

# These will be set by init_projects_blueprint
config_manager = None
indexer_status_ref = None

def init_projects_blueprint(cfg_manager, idx_status_ref):
    global config_manager, indexer_status_ref
    config_manager = cfg_manager
    indexer_status_ref = idx_status_ref

def get_dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except Exception:
                pass
    return total

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """Get list of projects with metadata"""
    projects_dict = config_manager.get_all_projects()
    projects_list = []

    # Build a lookup from indexer status
    indexer_status_map = {}
    try:
        for p in (indexer_status_ref.get("projects", []) if indexer_status_ref else []):
            indexer_status_map[p.get("path")] = p
    except Exception:
        pass

    if not projects_dict:
        projects_dict = {}
    for name, path in projects_dict.items():
        size = 0
        try:
            size = get_dir_size(path)
        except Exception:
            pass

        status_info = indexer_status_map.get(path, {})

        project_info = {
            "name": name,
            "path": path,
            "status": status_info.get("status", "idle"),
            "size": status_info.get("size", size),
            "lastIndexed": status_info.get("lastIndexed"),
            "error": status_info.get("error")
        }
        projects_list.append(project_info)

    return jsonify({"projects": projects_list})

@projects_bp.route('/', methods=['POST'])
def add_project():
    """Add a project"""
    data = request.json

    if not data or "path" not in data:
        return jsonify({"error": "Missing project path"}), 400

    project_path = data["path"]
    project_name = data.get("name")

    # Sanitize project_path: trim and remove surrounding quotes
    cleaned_path = project_path.strip().strip('"').strip("'")

    # Reject if suspicious or empty
    if not cleaned_path or '"' in cleaned_path or "'" in cleaned_path:
        return jsonify({"error": "Invalid project path format"}), 400

    try:
        # Check if path is already registered to provide a more specific message
        existing_projects = config_manager.get_all_projects()
        if existing_projects is None:
            existing_projects = {}

        if cleaned_path in existing_projects.values():
            # Find the name associated with this path
            existing_name = next((name for name, path in existing_projects.items() if path == cleaned_path), None)
            message = f"Project path '{cleaned_path}' is already registered as '{existing_name}'."
            return jsonify({"status": "success", "message": message})

        # If not registered, initialize it
        success = config_manager.initialize_project(cleaned_path, project_name)

        if success:
            # Get the final name assigned by initialize_project
            final_name = project_name or os.path.basename(cleaned_path)
            updated_projects = config_manager.get_all_projects()
            if updated_projects is None:
                updated_projects = {}

            # Find the final name, using the initial guess as fallback
            final_name = next((name for name, path in updated_projects.items() if path == os.path.abspath(cleaned_path)), final_name)

            # Trigger reindexing for the new project
            import requests
            try:
                resp = requests.post(
                    "http://localhost:5001/reindex",
                    json={"project_name": final_name},
                    timeout=2
                )
                if resp.ok:
                    reindex_msg = " and reindex triggered."
                else:
                    reindex_msg = f" but failed to trigger reindex: {resp.text}"
            except Exception as e:
                reindex_msg = f" but failed to trigger reindex: {e}"

            return jsonify({
                "status": "success",
                "message": f"Project '{final_name}' initialized successfully at '{cleaned_path}'{reindex_msg}"
            })
        else:
            return jsonify({"status": "error", "message": f"Failed to initialize project at '{cleaned_path}'."}), 500

    except FileNotFoundError:
        return jsonify({"status": "error", "message": f"Project path '{cleaned_path}' does not exist or is not accessible."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

@projects_bp.route('/<name>', methods=['DELETE'])
def remove_project(name):
    """Remove a project"""
    success = config_manager.remove_project(name)

    if success:
        return jsonify({"status": "success", "message": f"Removed project: {name}"})
    else:
        return jsonify({"error": f"Failed to remove project: {name}"}), 404

@projects_bp.route('/<project_name>/reindex', methods=['POST'])
def reindex_project(project_name):
    """Trigger reindexing for a specific project"""
    if not project_name:
        return jsonify({"error": "Project name required"}), 400

    project_path = config_manager.get_project_path(project_name)
    if not project_path:
        return jsonify({"error": "Project not found"}), 404

    metadata_dir = config_manager.get_metadata_path(project_path)
    hash_cache_file = os.path.join(metadata_dir, "hash_cache.json")

    try:
        if os.path.exists(hash_cache_file):
            os.remove(hash_cache_file)
        # Notify the indexer process to trigger reindexing
        import requests
        try:
            indexer_host = config_manager.config.get("indexer", {}).get("host", "localhost")
            indexer_port = config_manager.config.get("indexer", {}).get("port", 6656)
            indexer_url = f"http://{indexer_host}:{indexer_port}/reindex"
            resp = requests.post(
                indexer_url,
                json={"project_name": project_name},
                timeout=2
            )
            if resp.ok:
                return jsonify({"status": "success", "message": f"Reindex triggered for project {project_name}"})
            else:
                return jsonify({"status": "error", "message": f"Failed to notify indexer: {resp.text}"}), 500
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to notify indexer: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to trigger reindex: {e}"}), 500

@projects_bp.route('/active', methods=['GET'])
def get_active_project():
    """Get active project"""
    active_name = config_manager.get_active_project_name()
    projects = config_manager.get_all_projects()
    if active_name and active_name in projects:
        return jsonify({
            "project": {
                "name": active_name,
                "path": projects[active_name]
            }
        })
    else:
        return jsonify({"project": None})

@projects_bp.route('/active', methods=['POST'])
def set_active_project():
    """Set active project"""
    data = request.json

    if not data or "name" not in data:
        return jsonify({"error": "Missing project name"}), 400

    project_name = data["name"]
    projects = config_manager.get_all_projects()
    if project_name not in projects:
        return jsonify({"error": "Project not found"}), 404

    config_manager.set_active_project_name(project_name)
    # Hot-reload project-specific components
    try:
        # The actual reload logic should be handled by the orchestrator/server, not here.
        pass
    except Exception as e:
        return jsonify({"error": f"Failed to reload project components: {e}"}), 500
    return jsonify({"status": "success", "message": f"Set active project: {project_name}"})