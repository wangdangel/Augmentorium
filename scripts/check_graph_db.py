import sqlite3

db_path = r"K:\Documents\icecrawl\.Augmentorium\code_graph.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Nodes:")
for row in c.execute("SELECT id, type, name, file_path, start_line, end_line, metadata FROM nodes"):
    print(row)

print("\nEdges:")
for row in c.execute("SELECT source_id, target_id, relation_type, metadata FROM edges"):
    print(row)

conn.close()
