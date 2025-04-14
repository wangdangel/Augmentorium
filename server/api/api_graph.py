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
    for row in node_rows:
        node = {
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "file_path": row[3],
            "start_line": row[4],
            "end_line": row[5],
            "group": row[1] or "node",  # Use type as group for coloring
        }
        nodes.append(node)
    # Fetch all edges
    edge_rows = conn.execute("SELECT source_id, target_id, relation_type, metadata FROM edges").fetchall()
    links = []
    for row in edge_rows:
        link = {
            "source": row[0],
            "target": row[1],
            "relation": row[2],
        }
        links.append(link)
    conn.close()
    graph = {
        "nodes": nodes,
        "links": links,
    }
    return jsonify(graph)