from flask import Blueprint, jsonify, request

indexer_bp = Blueprint('indexer', __name__, url_prefix='/api/indexer')

# Module-level variable to store indexer status (not production-safe, for migration only)
indexer_status = {}

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
        global indexer_status
        indexer_status = data
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500