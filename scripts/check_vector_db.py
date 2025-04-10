import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db_utils import VectorDB

project_root = r"K:\Documents\icecrawl"
db_path = os.path.join(project_root, ".augmentorium", "chroma_db")

vector_db = VectorDB(db_path)

collections = vector_db.list_collections()
print("Collections:", collections)

for collection in collections:
    print(f"\nCollection: {collection}")
    docs = vector_db.get_documents(collection_name=collection)
    for doc in docs.get("documents", []):
        print(doc)
