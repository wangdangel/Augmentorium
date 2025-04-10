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
