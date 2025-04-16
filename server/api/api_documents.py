from flask import Blueprint, jsonify, request, current_app, g
import os
import logging

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
logger = logging.getLogger(__name__)

def get_config_manager():
    # Try g first, fallback to current_app
    config_manager = getattr(g, "config_manager", None)
    if config_manager is None:
        config_manager = getattr(current_app, "config_manager", None)
    return config_manager

@documents_bp.route('/', methods=['GET'])
def list_documents():
    """
    List indexed documents for a specific project.
    Requires: project name in query params.
    """
    project_name = request.args.get("project")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    config_manager = get_config_manager()
    # TODO: Replace with real document metadata retrieval for the given project
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
def upload_document():
    """
    Upload a new document to a specific project.
    Requires: project name in request JSON.
    """
    data = request.json or {}
    project_name = data.get("project")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    # TODO: Implement file upload handling for the given project
    return jsonify({"status": "success", "message": f"Upload endpoint not yet implemented for project {project_name}"}), 501


@documents_bp.route('/<doc_id>/reindex', methods=['POST'])
def reindex_document(doc_id):
    """
    Trigger reindexing of a specific document for a given project.
    Requires: project name in request JSON.
    """
    data = request.json or {}
    project_name = data.get("project")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    # TODO: Implement per-document reindexing for the given project
    return jsonify({"status": "success", "message": f"Reindex {doc_id} not yet implemented for project {project_name}"}), 501