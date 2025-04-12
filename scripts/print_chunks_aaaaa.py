import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db_utils import VectorDB
from indexer.embedder import OllamaEmbedder

DB_PATH = r"K:\Documents\aaaaa\.Augmentorium\chroma"

def main():
    vector_db = VectorDB(DB_PATH)
    collections = vector_db.list_collections()
    print("Collections:", collections)
    for collection in collections:
        print(f"\nCollection: {collection}")
        docs = vector_db.get_documents(collection_name=collection, limit=3, include=["documents", "metadatas", "embeddings"])
        documents = docs.get("documents", [])
        embeddings = docs.get("embeddings", [])
        print(f"Number of documents: {len(documents)}")
        for i, doc_text in enumerate(documents):
            print(f"\n--- Chunk {i+1} ---")
            print(doc_text)
            if embeddings is not None and len(embeddings) > i:
                emb = embeddings[i]
                if emb is not None:
                    print(f"Embedding length: {len(emb)}")
                    print(f"First 10 embedding values: {emb[:10]}")
                else:
                    print("Embedding: None")
        if not documents:
            print("No documents found in this collection.")

    # Compare with current embedder
    print("\n--- Embedding length for sample query using current OllamaEmbedder ---")
    embedder = OllamaEmbedder()
    sample_query = "app.route"
    query_emb = embedder.get_embedding(sample_query)
    if query_emb is not None:
        print(f"Sample query embedding length: {len(query_emb)}")
        print(f"First 10 query embedding values: {query_emb[:10]}")
        # Directly query the vector DB for this embedding
        print("\n--- Raw vector DB query results for 'app.route' ---")
        results = vector_db.query(
            collection_name=collections[0],
            query_embeddings=[query_emb],
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )
        print("Raw results:", results)
        if "distances" in results and results["distances"]:
            print("\n--- Distances for top results ---")
            for i, dist in enumerate(results["distances"][0]):
                print(f"Result {i+1}: distance={dist} (score={1.0 - dist})")
    else:
        print("Failed to get embedding for sample query.")

if __name__ == "__main__":
    main()
