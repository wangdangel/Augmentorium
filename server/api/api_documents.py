from flask import Blueprint, jsonify, request, current_app, g
import os
import logging

from server.api.common import require_active_project

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
logger = logging.getLogger(__name__)

def get_config_manager():
    # Try g first, fallback to current_app
    config_manager = getattr(g, "config_manager", None)
    if config_manager is None:
        config_manager = getattr(current_app, "config_manager", None)
    return config_manager

@documents_bp.route('/', methods=['GET'])
@require_active_project
def list_documents():
    """
    List indexed documents.
    """
    config_manager = get_config_manager()
    # TODO: Replace with real document metadata retrieval
    docs = [
        {
            "id": "doc1",
            "name": "example.py",
            "size": 12345,
            "uploaded_at": "2024-01-01T12:00:00Z",
            "status": "indexed",
            "chunkCount": 10,
            "lastIndexed": "2024-01-01T12:05:00Z"
        }
    ]
    return jsonify({"documents": docs})

@documents_bp.route('/upload', methods=['POST'])
@require_active_project
def upload_document():
    """
    Upload a new document.
    """
    # TODO: Implement file upload handling
    return jsonify({"status": "success", "message": "Upload endpoint not yet implemented"}), 501


@documents_bp.route('/<doc_id>/reindex', methods=['POST'])
@require_active_project
def reindex_document(doc_id):
    """
    Trigger reindexing of a specific document.
    """
    # TODO: Implement per-document reindexing
    return jsonify({"status": "success", "message": f"Reindex {doc_id} not yet implemented"}), 501