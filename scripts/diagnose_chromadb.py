import chromadb
from utils.db_utils import get_chroma_db_path

def main(project_path):
    # Connect to local ChromaDB
    chroma_path = get_chroma_db_path(project_path)  # project_path must be defined or passed in
    client = chromadb.PersistentClient(path=chroma_path)
    
    collections = client.list_collections()
    if not collections:
        print("No collections found in ChromaDB.")
        return
    
    for coll in collections:
        print(f"Collection: {coll.name}")
        count = coll.count()
        print(f"  Number of documents: {count}")
        if count == 0:
            continue
        # Fetch sample documents
        sample = coll.peek(5)
        for i, doc in enumerate(sample):
            print(f"  Sample #{i+1}:")
            print(f"    Content: {doc[:200]}...")
            print()

if __name__ == "__main__":
    main(project_path)  # project_path must be defined or passed in
