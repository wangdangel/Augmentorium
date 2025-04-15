# check_chroma_collections.py
from utils.db_utils import get_chroma_db_path, VectorDB
import os

# Updated path to match actual ChromaDB location
project_path = r"K:\Documents\icecrawl"
chroma_db_path = get_chroma_db_path(project_path)

if not os.path.exists(chroma_db_path):
    print(f"Chroma DB directory does not exist: {chroma_db_path}")
    exit(1)
else:
    db = VectorDB(chroma_db_path)

    print("Collections:")
    print(db.list_collections())

    print("\nCollection stats for 'code_chunks':")
    print(db.get_collection_stats("code_chunks"))
