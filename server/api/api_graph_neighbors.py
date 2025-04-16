from flask import Blueprint, request, jsonify, current_app, g
from server.api.project_helpers import get_project_path
from server.query import RelationshipEnricher

graph_neighbors_bp = Blueprint('graph_neighbors', __name__, url_prefix='/api/graph/neighbors')

@graph_neighbors_bp.route('/', methods=['POST'])
def get_neighbors():
    """
    Given a node (function/class/file), return its graph neighbors (callers, callees, imports, etc.).
    Request: { "project": str (required), "node_id": str }
    Response: { "neighbors": [ ... ] }
    """
    data = request.json or {}
    project_name = data.get("project")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    node_id = data.get("node_id")
    if not node_id:
        return jsonify({"error": "node_id must be specified"}), 400

    config_manager = getattr(g, "config_manager", None)
    if config_manager is None:
        config_manager = getattr(current_app, "config_manager", None)
    if config_manager is None:
        return jsonify({"error": "No config manager found"}), 500

    project_path = get_project_path(config_manager, project_name)
    if not project_path:
        return jsonify({"error": "Project not found"}), 404

    # Get the correct graph DB path for this project
    graph_db_path = config_manager.get_graph_db_path(project_path)
    if not graph_db_path:
        return jsonify({"error": "Could not resolve graph DB path for project"}), 500

    # Instantiate RelationshipEnricher for this request/project
    relationship_enricher = RelationshipEnricher(
        vector_db=None,  # Not needed for neighbors
        collection_name=None,  # Not needed for neighbors
        graph_db_path=graph_db_path
    )

    # Use the RelationshipEnricher.get_neighbors method
    neighbors = relationship_enricher.get_neighbors(node_id)
    return jsonify({"neighbors": neighbors})
