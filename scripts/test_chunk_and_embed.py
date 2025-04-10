import os
import sys
import yaml
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from indexer.chunker import Chunker
from indexer.embedder import OllamaEmbedder
from utils.db_utils import VectorDB
from utils.graph_db import get_connection, insert_or_update_node, insert_edge

def load_ollama_config(config_path="config.yaml"):
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        ollama_cfg = config.get("ollama", {})
        return {
            "base_url": ollama_cfg.get("base_url", "http://localhost:11434"),
            "embedding_model": ollama_cfg.get("embedding_model", "codellama"),
            "embedding_batch_size": ollama_cfg.get("embedding_batch_size", 10)
        }
    except Exception:
        return {
            "base_url": "http://localhost:11434",
            "embedding_model": "codellama",
            "embedding_batch_size": 10
        }

def main():
    project_root = r"K:\Documents\icecrawl"
    target_file = os.path.join("scripts", "diagnose_chromadb.py")
    if not os.path.exists(target_file):
        print(f"File not found: {target_file}")
        return

    print(f"Chunking file: {target_file}")
    chunker = Chunker()
    chunks = chunker.chunk_file(target_file)
    print(f"Total chunks: {len(chunks)}\n")

    ollama_cfg = load_ollama_config()
    embedder = OllamaEmbedder(
        base_url=ollama_cfg["base_url"],
        model=ollama_cfg["embedding_model"],
        batch_size=ollama_cfg["embedding_batch_size"]
    )

    # Prepare data for vector DB
    documents = []
    metadatas = []
    ids = []
    embeddings = []

    for idx, chunk in enumerate(chunks):
        print(f"--- Chunk #{idx+1} ---")
        print(f"ID: {chunk.id}")
        print(f"Type: {chunk.chunk_type}")
        print(f"Name: {chunk.name}")
        print(f"Lines: {chunk.start_line}-{chunk.end_line}")
        print(f"Metadata: {chunk.metadata}")
        print(f"Text (first 200 chars):\n{chunk.text[:200]}...\n")

        embedding = embedder.get_embedding(chunk.text)
        if embedding:
            print(f"Embedding length: {len(embedding)}")
            print(f"Embedding sample: {embedding[:5]}\n")
        else:
            print("Embedding: None\n")

        documents.append(chunk.text)
        # Flatten metadata lists to comma-separated strings
        flat_meta = {}
        for k, v in chunk.metadata.items():
            if isinstance(v, list):
                flat_meta[k] = ", ".join(str(item) for item in v)
            elif v is None:
                flat_meta[k] = ""
            else:
                flat_meta[k] = v
        metadatas.append(flat_meta)
        ids.append(chunk.id)
        embeddings.append(embedding)

    # Insert into vector DB
    db_path = os.path.join(project_root, ".augmentorium", "chroma_db")
    os.makedirs(db_path, exist_ok=True)
    vector_db = VectorDB(db_path)
    success = vector_db.upsert_documents(
        collection_name="code_chunks",
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )
    print(f"Vector DB upsert success: {success}")

    # Insert into graph DB
    graph_db_path = os.path.join(project_root, ".augmentorium", "code_graph.db")
    conn = get_connection(graph_db_path)
    for chunk in chunks:
        node_data = {
            "id": chunk.id,
            "type": chunk.chunk_type,
            "name": chunk.name,
            "file_path": chunk.file_path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "metadata": chunk.metadata
        }
        insert_or_update_node(conn, node_data)

        refs = chunk.metadata.get("references", [])
        for ref in refs:
            insert_edge(conn, chunk.id, ref, "references")

    conn.commit()
    conn.close()
    print(f"Graph DB updated at {graph_db_path}")

if __name__ == "__main__":
    main()
