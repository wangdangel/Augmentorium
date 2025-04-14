import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db_utils import VectorDB

project_root = r"K:\Documents\icecrawl"
db_path = os.path.join(project_root, ".Augmentorium", "chroma")

vector_db = VectorDB(db_path)

collections = vector_db.list_collections()
print("Collections:", collections)

for collection in collections:
    print(f"\nCollection: {collection}")
    stats = vector_db.get_collection_stats(collection)
    print(f"  Document count: {stats.get('count', 0)}")
    docs = vector_db.get_documents(collection_name=collection, limit=3)
    doc_ids = docs.get("ids", [])
    documents = docs.get("documents", [])
    metadatas = docs.get("metadatas", [])
    if not doc_ids:
        print("  No documents found in this collection.")
    else:
        print("  Sample documents:")
        for i, doc_id in enumerate(doc_ids):
            doc_text = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if i < len(metadatas) else {}
            snippet = doc_text[:100].replace("\n", " ") + ("..." if len(doc_text) > 100 else "")
            print(f"    - ID: {doc_id}, Text: \"{snippet}\", Metadata: {meta}")
