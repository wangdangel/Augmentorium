from flask import Blueprint, jsonify, request

indexer_bp = Blueprint('indexer', __name__, url_prefix='/api/indexer')

# Shared object to store indexer status (set by init_indexer_blueprint)
indexer_status_ref = None

def init_indexer_blueprint(shared_status):
    global indexer_status_ref
    indexer_status_ref = shared_status

@indexer_bp.route('/', methods=['GET'])
def indexer_placeholder():
    return jsonify({"status": "ok"})

@indexer_bp.route('/status', methods=['POST'])
def update_indexer_status():
    """Receive status update from indexer"""
    try:
        data = request.json
        if not data or "projects" not in data:
            return jsonify({"error": "Invalid status update"}), 400
        global indexer_status_ref
        if indexer_status_ref is not None:
            # Update the shared object in-place
            indexer_status_ref.clear()
            indexer_status_ref.update(data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@indexer_bp.route('/status', methods=['GET'])
def get_indexer_status():
    """Return the current indexer status as JSON"""
    global indexer_status_ref
    if indexer_status_ref is not None:
        return jsonify(indexer_status_ref)
    else:
        return jsonify({})