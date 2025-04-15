from flask import Blueprint, jsonify, Response, current_app

graph_bp = Blueprint('graph', __name__, url_prefix='/api/graph')

@graph_bp.route('/', methods=['GET'])
def get_graph() -> Response:
    config_manager = current_app.config_manager
    active_project = config_manager.get_active_project_name()
    if not active_project:
        return (
            jsonify({
                "error": "No active project set. Please set or create a project using the /api/projects endpoint."
            }),
            400
        )
    """
    Return code relationship graph data from the graph database.

    Error Response (if no active project):
        HTTP 400
        {
            "error": "No active project set. Please set or create a project using the /api/projects endpoint."
        }
    """
    from utils.graph_db import get_connection
    import json
    # Get the active project path and graph DB path
    project_path = config_manager.get_project_path(active_project)
    graph_db_path = config_manager.get_graph_db_path(project_path)
    conn = get_connection(graph_db_path)
    # Fetch all nodes
    node_rows = conn.execute("SELECT id, type, name, file_path, start_line, end_line, metadata FROM nodes").fetchall()
    nodes = []
    node_ids = set()
    for row in node_rows:
        node = {
            "id": row[0],
            "type": row[1],
            "name": row[2] or row[3] or row[0],  # Prefer name, then file_path, then id
            "file_path": row[3],
            "start_line": row[4],
            "end_line": row[5],
            "group": row[1] or "node",  # Use type as group for coloring
        }
        nodes.append(node)
        node_ids.add(row[0])
    # Fetch all edges
    edge_rows = conn.execute("SELECT source_id, target_id, relation_type, metadata FROM edges").fetchall()
    links = []
    external_nodes = {}
    for row in edge_rows:
        src, tgt, rel = row[0], row[1], row[2]
        # If target node doesn't exist, add as external dependency
        if tgt not in node_ids:
            if tgt not in external_nodes:
                ext_node = {
                    "id": tgt,
                    "type": "external",
                    "name": tgt,
                    "file_path": None,
                    "start_line": None,
                    "end_line": None,
                    "group": "external",
                }
                external_nodes[tgt] = ext_node
        # Only include links where source exists
        if src in node_ids:
            link = {
                "source": src,
                "target": tgt,
                "relation": rel,
            }
            links.append(link)
    # Add all external nodes
    nodes.extend(external_nodes.values())
    conn.close()
    graph = {
        "nodes": nodes,
        "links": links,
    }
    return jsonify(graph)