import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from utils.db_utils import VectorDB
from indexer.embedder import OllamaEmbedder

# Config
OLLAMA_URL = "http://10.0.0.246:11434/api/embeddings"
from config.manager import ConfigManager

config = ConfigManager()
ollama_config = config.config.get("ollama", {})
EMBEDDING_MODEL = ollama_config.get("embedding_model", "bge-m3:latest")
PROJECT_ROOT = r"K:\\Documents\\icecrawl"
DB_PATH = os.path.join(PROJECT_ROOT, ".Augmentorium", "chroma")
COLLECTION_NAME = "code_chunks"

# Use the full text of the first document in the vector DB as the test input
def get_first_document_text():
    vector_db = VectorDB(DB_PATH)
    docs = vector_db.get_documents(collection_name=COLLECTION_NAME, limit=1)
    documents = docs.get("documents", [])
    if documents:
        return documents[0]
    return None

def get_embedding_from_ollama(text):
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    resp = requests.post(OLLAMA_URL, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data.get("embedding")

def get_embedding_from_backend(text):
    embedder = OllamaEmbedder()
    return embedder.get_embedding(text)

def get_stored_embedding(text):
    vector_db = VectorDB(DB_PATH)
    docs = vector_db.get_documents(collection_name=COLLECTION_NAME, limit=10000, include=["documents", "embeddings"])
    documents = docs.get("documents", [])
    embeddings = docs.get("embeddings", None)
    if not documents or embeddings is None:
        return None
    # If embeddings is a numpy array, convert to list of lists
    try:
        import numpy as np
        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()
    except ImportError:
        pass
    for i, doc_text in enumerate(documents):
        if doc_text == text:
            return embeddings[i]
    return None

def print_embedding_info(name, emb):
    if emb is None:
        print(f"{name}: None")
        return
    print(f"{name}:")
    print(f"  Type: {type(emb)}")
    print(f"  Length: {len(emb)}")
    if hasattr(emb, 'dtype'):
        print(f"  Dtype: {emb.dtype}")
    print(f"  First 20 values: {json.dumps(emb[:20])} ...")

def main():
    test_text = get_first_document_text()
    if not test_text:
        print("No documents found in the collection.")
        return

    print("Testing embedding serialization for the first document in the vector DB:")
    print(test_text[:200] + ("..." if len(test_text) > 200 else ""))
    print("="*60)

    emb_ollama = get_embedding_from_ollama(test_text)
    emb_backend = get_embedding_from_backend(test_text)
    emb_stored = get_stored_embedding(test_text)

    print_embedding_info("1. Embedding from Ollama API", emb_ollama)
    print_embedding_info("2. Embedding from backend OllamaEmbedder", emb_backend)
    print_embedding_info("3. Embedding as stored in vector DB", emb_stored)

    # Optionally, compare for equality
    if emb_ollama and emb_backend:
        same = all(abs(a - b) < 1e-6 for a, b in zip(emb_ollama, emb_backend))
        print(f"\nOllama API and backend embedding identical? {same}")
    if emb_backend and emb_stored:
        same2 = all(abs(a - b) < 1e-6 for a, b in zip(emb_backend, emb_stored))
        print(f"Backend and stored embedding identical? {same2}")

if __name__ == "__main__":
    main()
