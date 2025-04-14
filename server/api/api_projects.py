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
    if config_manager:
        success = config_manager.set_active_project_name(project_name)
        if success:
            return jsonify({"status": "success", "message": f"Active project set to '{project_name}'"})
        else:
            all_projects = config_manager.get_all_projects()
            if project_name not in all_projects:
                return jsonify({"error": f"Project '{project_name}' not found."}), 404
            else:
                return jsonify({"error": f"Failed to set active project to '{project_name}'."}), 500
    else:
        return jsonify({"error": "Configuration manager not available"}), 500

@projects_bp.route('/<project_name>/reinitialize', methods=['POST'])
def reinitialize_project(project_name):
    print(f"[DEBUG] reinitialize_project called for project: {project_name}")
    """
    Reinitialize a project:
    - Delete the .Augmentorium folder and all its contents
    - Recreate .Augmentorium, the soldier, and the graph database
    - Trigger the indexer to re-index the project
    """
    import shutil

    if not project_name:
        return jsonify({"status": "error", "message": "Project name required"}), 400

    # 1. Look up the project path
    project_path = config_manager.get_project_path(project_name)
    if not project_path:
        return jsonify({"status": "error", "message": "Project not found"}), 404

    # 2. Pause the indexer before deleting .Augmentorium
    from config.defaults import PROJECT_INTERNAL_DIR_NAME
    augmentorium_path = os.path.join(project_path, PROJECT_INTERNAL_DIR_NAME)
    indexer_host = config_manager.config.get("indexer", {}).get("host", "localhost")
    indexer_port = config_manager.config.get("indexer", {}).get("port", 6656)
    pause_url = f"http://{indexer_host}:{indexer_port}/pause"
    import requests
    print(f"[DEBUG] Sending pause request to indexer at {pause_url}")
    try:
        pause_resp = requests.post(pause_url, json={"project_name": project_name}, timeout=2)
        if not pause_resp.ok:
            print(f"[ERROR] Indexer /pause failed: {pause_resp.text}")
            return jsonify({"status": "error", "message": f"Failed to pause indexer: {pause_resp.text}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception during indexer /pause: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Exception during indexer pause: {e}"}), 500
    
    # 3. Delete the .Augmentorium folder with retry and diagnostics
    import time
    print(f"[DEBUG] Attempting to delete {augmentorium_path} (with retry and diagnostics)")
    max_attempts = 5
    attempt = 0
    last_exception = None
    while attempt < max_attempts:
        try:
            if os.path.exists(augmentorium_path):
                shutil.rmtree(augmentorium_path)
                print(f"[DEBUG] Successfully deleted {augmentorium_path} on attempt {attempt+1}")
            else:
                print(f"[DEBUG] {augmentorium_path} does not exist, skipping deletion")
            break
        except Exception as e:
            print(f"[ERROR] Exception deleting {augmentorium_path} on attempt {attempt+1}: {e}")
            last_exception = e
            # Try to diagnose which process is holding the file (Windows only)
            try:
                import sys
                if sys.platform == "win32":
                    try:
                        import psutil
                        locked_file = None
                        # Find the first file that is locked
                        for dirpath, dirnames, filenames in os.walk(augmentorium_path):
                            for f in filenames:
                                fp = os.path.join(dirpath, f)
                                try:
                                    with open(fp, "a"):
                                        pass
                                except Exception as file_exc:
                                    locked_file = fp
                                    print(f"[DIAG] File locked: {fp} ({file_exc})")
                                    # Try to find which process is holding it
                                    for proc in psutil.process_iter(['pid', 'name']):
                                        try:
                                            for item in proc.open_files():
                                                if item.path == fp:
                                                    print(f"[DIAG] Process {proc.pid} ({proc.name()}) is holding {fp}")
                                        except Exception:
                                            continue
                                    break
                            if locked_file:
                                break
                    except ImportError:
                        print("[DIAG] psutil not installed, cannot check open file handles.")
            except Exception as diag_exc:
                print(f"[DIAG] Exception during diagnostics: {diag_exc}")
            attempt += 1
            if attempt < max_attempts:
                print(f"[DEBUG] Waiting before retrying delete (attempt {attempt+1})...")
                time.sleep(0.5)
            else:
                print(f"[ERROR] Max delete attempts reached for {augmentorium_path}")
                import traceback
                traceback.print_exc()
                return jsonify({"status": "error", "message": f"Failed to delete {PROJECT_INTERNAL_DIR_NAME} after {max_attempts} attempts: {last_exception}"}), 500

    # 3. Recreate .Augmentorium, soldier, and graph DB
    print(f"[DEBUG] Attempting to initialize project at {project_path} with name {project_name}")
    try:
        success = config_manager.initialize_project(project_path, project_name)
        print(f"[DEBUG] initialize_project returned: {success}")
        if not success:
            print(f"[ERROR] initialize_project returned False for {project_path}, {project_name}")
            return jsonify({"status": "error", "message": f"Failed to reinitialize project at '{project_path}'."}), 500
    except Exception as e:
        print(f"[ERROR] Exception in initialize_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Failed to reinitialize project: {e}"}), 500
    # 4. Resume the indexer after reinitialization
    resume_url = f"http://{indexer_host}:{indexer_port}/resume"
    print(f"[DEBUG] Sending resume request to indexer at {resume_url}")
    try:
        resume_resp = requests.post(resume_url, json={"project_name": project_name}, timeout=2)
        if not resume_resp.ok:
            print(f"[ERROR] Indexer /resume failed: {resume_resp.text}")
            return jsonify({"status": "error", "message": f"Failed to resume indexer: {resume_resp.text}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception during indexer /resume: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Exception during indexer resume: {e}"}), 500

    # 5. Trigger the indexer to re-index the project
    try:
        indexer_url = f"http://{indexer_host}:{indexer_port}/reindex"
        resp = requests.post(
            indexer_url,
            json={"project_name": project_name},
            timeout=2
        )
        if resp.ok:
            reindex_msg = " and reindex triggered."
        else:
            reindex_msg = f" but failed to trigger reindex: {resp.text}"
    except Exception as e:
        reindex_msg = f" but failed to trigger reindex: {e}"

    # 6. Return a success message
    return jsonify({
        "status": "success",
        "message": f"Project '{project_name}' reinitialized successfully at '{project_path}'{reindex_msg}"
    })
