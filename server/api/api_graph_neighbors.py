from flask import Blueprint, request, jsonify, current_app, g
from server.api.project_helpers import get_project_path
from server.query import RelationshipEnricher

graph_neighbors_bp = Blueprint('graph_neighbors', __name__, url_prefix='/api/graph/neighbors')

@graph_neighbors_bp.route('/', methods=['POST'])
def get_neighbors():
    """
    Given a node (function/class/file), return its graph neighbors (callers, callees, imports, etc.).
    Request: { "project": str (required), "node_id": str, "file_name": str (optional) }
    Response: { "neighbors": [ ... ] }
    """
    data = request.json or {}
    project_name = data.get("project")
    file_name = data.get("file_name")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    node_id = data.get("node_id")
    # If node_id is not provided but file_name is, look up node(s) by file_name
    if not node_id and file_name:
        # Use graph_db to look up node(s) by file name
        config_manager = getattr(g, "config_manager", None)
        if config_manager is None:
            config_manager = getattr(current_app, "config_manager", None)
        if config_manager is None:
            return jsonify({"error": "No config manager found"}), 500
        project_path = get_project_path(config_manager, project_name)
        if not project_path:
            return jsonify({"error": "Project not found"}), 404
        graph_db_path = config_manager.get_graph_db_path(project_path)
        if not graph_db_path:
            return jsonify({"error": "Could not resolve graph DB path for project"}), 500
        from utils.graph_db import get_nodes_by_file_path
        import os
        import sqlite3
        conn = sqlite3.connect(graph_db_path)
        nodes = get_nodes_by_file_path(conn, file_name)
        if not nodes:
            # Try basename match
            all_nodes = conn.execute("SELECT id, file_path FROM nodes").fetchall()
            for row in all_nodes:
                if row[1] and os.path.basename(row[1]) == file_name:
                    nodes.append({"id": row[0]})
        if not nodes:
            conn.close()
            return jsonify({"error": f"No nodes found for file name '{file_name}'."}), 404
        node_ids = [n["id"] for n in nodes]
        conn.close()
    elif not node_id:
        return jsonify({"error": "node_id or file_name must be specified"}), 400
    else:
        node_ids = [node_id]

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

    # Use the RelationshipEnricher.get_neighbors method for each node_id
    all_neighbors = []
    for nid in node_ids:
        neighbors = relationship_enricher.get_neighbors(nid)
        all_neighbors.extend(neighbors)
    return jsonify({"neighbors": all_neighbors})
