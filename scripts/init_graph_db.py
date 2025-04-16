import sqlite3
import os

def init_graph_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create nodes table
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

    # Create edges table
    c.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        metadata TEXT
    )
    """)

    # Indexes for fast lookup
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)")

    conn.commit()
    conn.close()
    print(f"Graph database initialized at {db_path}")

if __name__ == "__main__":
    # Example: initialize graph DB for a project
    graph_db_path = r"K:\Documents\icecrawl\.Augmentorium\code_graph.db"
    init_graph_db(graph_db_path)
