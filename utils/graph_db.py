import sqlite3
import json
import os

def get_connection(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)

def insert_or_update_node(conn, node):
    """
    node: dict with keys id, type, name, file_path, start_line, end_line, metadata (dict)
    """
    metadata_json = json.dumps(node.get("metadata", {}))
    conn.execute("""
    INSERT INTO nodes (id, type, name, file_path, start_line, end_line, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        type=excluded.type,
        name=excluded.name,
        file_path=excluded.file_path,
        start_line=excluded.start_line,
        end_line=excluded.end_line,
        metadata=excluded.metadata
    """, (
        node["id"],
        node.get("type"),
        node.get("name"),
        node.get("file_path"),
        node.get("start_line"),
        node.get("end_line"),
        metadata_json
    ))

def insert_edge(conn, source_id, target_id, relation_type, metadata=None):
    metadata_json = json.dumps(metadata or {})
    conn.execute("""
    INSERT INTO edges (source_id, target_id, relation_type, metadata)
    VALUES (?, ?, ?, ?)
    """, (source_id, target_id, relation_type, metadata_json))

def delete_node(conn, node_id):
    conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    conn.execute("DELETE FROM edges WHERE source_id = ? OR target_id = ?", (node_id, node_id))

def delete_edges_for_node(conn, node_id):
    conn.execute("DELETE FROM edges WHERE source_id = ? OR target_id = ?", (node_id, node_id))


def initialize_graph_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        type TEXT,
        name TEXT,
        file_path TEXT,
        start_line INTEGER,
        end_line INTEGER,
        metadata TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        metadata TEXT
    )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)")
    conn.commit()
    conn.close()

def get_edges_for_node(conn, node_id, relation_type=None):
    """
    Returns a list of edges for a given node_id (as source), optionally filtered by relation_type.
    Each edge is a dict with keys: source_id, target_id, relation_type, metadata (dict).
    """
    if relation_type:
        cursor = conn.execute(
            "SELECT source_id, target_id, relation_type, metadata FROM edges WHERE source_id = ? AND relation_type = ?",
            (node_id, relation_type)
        )
    else:
        cursor = conn.execute(
            "SELECT source_id, target_id, relation_type, metadata FROM edges WHERE source_id = ?",
            (node_id,)
        )
    edges = []
    for row in cursor.fetchall():
        edges.append({
            "source_id": row[0],
            "target_id": row[1],
            "relation_type": row[2],
            "metadata": json.loads(row[3]) if row[3] else {}
        })
    return edges

def get_node_by_id(conn, node_id):
    """
    Returns a node dict for the given node_id, or None if not found.
    """
    cursor = conn.execute(
        "SELECT id, type, name, file_path, start_line, end_line, metadata FROM nodes WHERE id = ?",
        (node_id,)
    )
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "file_path": row[3],
            "start_line": row[4],
            "end_line": row[5],
            "metadata": json.loads(row[6]) if row[6] else {}
        }
    return None

def get_nodes_by_file_path(conn, file_path):
    """
    Returns a list of node dicts for the given file_path.
    """
    cursor = conn.execute(
        "SELECT id, type, name, file_path, start_line, end_line, metadata FROM nodes WHERE file_path = ?",
        (file_path,)
    )
    nodes = []
    for row in cursor.fetchall():
        nodes.append({
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "file_path": row[3],
            "start_line": row[4],
            "end_line": row[5],
            "metadata": json.loads(row[6]) if row[6] else {}
        })
    return nodes
