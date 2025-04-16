import requests
import json

OLLAMA_URL = "http://10.0.0.246:11434/api/embeddings"
from config.manager import ConfigManager

config = ConfigManager()
ollama_config = config.config.get("ollama", {})
MODEL = ollama_config.get("embedding_model", "bge-m3:latest")
PROMPT = "test embedding string"

payload = {
    "model": MODEL,
    "prompt": PROMPT
}

try:
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    print("Embedding response:", json.dumps(data, indent=2))
except Exception as e:
    print("Error contacting Ollama embedding server:", e)
