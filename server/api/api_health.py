from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})