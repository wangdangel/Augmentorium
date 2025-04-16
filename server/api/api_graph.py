from flask import Blueprint, jsonify, Response, current_app, request

graph_bp = Blueprint('graph', __name__, url_prefix='/api/graph')

@graph_bp.route('/', methods=['GET', 'POST'])
def get_graph() -> Response:
    # Accept project as query param (GET) or in JSON body (POST)
    project_name = request.args.get('project')
    if not project_name and request.method == 'POST':
        data = request.get_json(silent=True) or {}
        project_name = data.get('project')
    if not project_name:
        return (
            jsonify({
                "error": "Project name must be specified as a query parameter or in the POST body."
            }),
            400
        )
    config_manager = getattr(current_app, 'config_manager', None)
    if config_manager is None:
        return jsonify({"error": "No config manager found"}), 500
    project_path = config_manager.get_project_path(project_name)
    if not project_path:
        return jsonify({"error": f"Project '{project_name}' not found."}), 404
    graph_db_path = config_manager.get_graph_db_path(project_path)
    if not graph_db_path:
        return jsonify({"error": f"Graph DB for project '{project_name}' not found."}), 404
    from utils.graph_db import get_connection
    import json
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