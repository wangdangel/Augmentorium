"""
Client for communicating with the Augmentorium RAG server via REST API.
"""
import httpx
from typing import List, Dict, Optional
import mcp_types as types

RAG_SERVER_URL = "http://localhost:6655"

# --- Project & File Endpoints ---
async def fetch_projects() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/api/projects/")
        resp.raise_for_status()
        return resp.json()

async def fetch_files(project: str, max_files: int = 20) -> List[Dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/api/files/?project={project}&max_files={max_files}")
        resp.raise_for_status()
        return resp.json()

async def fetch_documents(project: str) -> List[Dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/api/documents/?project={project}")
        resp.raise_for_status()
        return resp.json()

# --- Graph Endpoints ---
async def fetch_graph(project: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/api/graph/?project={project}")
        resp.raise_for_status()
        return resp.json()

async def fetch_graph_neighbors(project: str, node_id: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{RAG_SERVER_URL}/api/graph/neighbors/", json={"project": project, "node_id": node_id})
        resp.raise_for_status()
        return resp.json()

# --- Tool Endpoints ---
async def fetch_tools() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/tools")
        resp.raise_for_status()
        return resp.json()

async def fetch_tool(tool_name: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/tools/{tool_name}")
        resp.raise_for_status()
        return resp.json()

async def fetch_prompts() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/prompts")
        resp.raise_for_status()
        return resp.json()

async def fetch_prompt(prompt_name: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/prompts/{prompt_name}")
        resp.raise_for_status()
        return resp.json()

async def fetch_resources() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/resources")
        resp.raise_for_status()
        return resp.json()

async def fetch_resource(resource_id: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/resources/{resource_id}")
        resp.raise_for_status()
        return resp.json()

async def run_query(project: str, query: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{RAG_SERVER_URL}/api/query/", json={"project": project, "query": query})
        resp.raise_for_status()
        return resp.json()

async def upload_document(project: str, name: str, content: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{RAG_SERVER_URL}/api/documents/upload", json={"project": project, "name": name, "content": content})
        resp.raise_for_status()
        return resp.json()

async def explain(project: str, query: str, result: dict) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{RAG_SERVER_URL}/api/explain/", json={"project": project, "query": query, "result": result})
        resp.raise_for_status()
        return resp.json()

# --- Stats & Indexer ---
async def fetch_stats(project: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/api/stats/?project={project}")
        resp.raise_for_status()
        return resp.json()

async def fetch_indexer_status() -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RAG_SERVER_URL}/api/indexer/status")
        resp.raise_for_status()
        return resp.json()

# --- Indexer Actions ---
async def reindex_document(project: str, doc_id: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{RAG_SERVER_URL}/api/documents/{doc_id}/reindex", json={"project": project})
        resp.raise_for_status()
        return resp.json()

async def update_indexer_status(projects: list[str]) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{RAG_SERVER_URL}/api/indexer/status", json={"projects": projects})
        resp.raise_for_status()
        return resp.json()

# --- Chunk Search ---
async def search_chunks(project: str, query: str, n_results: int = 5) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{RAG_SERVER_URL}/api/chunks/search", json={"project": project, "query": query, "n_results": n_results})
        resp.raise_for_status()
        return resp.json()

# --- Caches ---
async def clear_query_cache(project: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{RAG_SERVER_URL}/api/query/cache?project={project}")
        resp.raise_for_status()
        return resp.json()

async def clear_general_cache(project: str) -> Dict:
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{RAG_SERVER_URL}/api/cache/?project={project}")
        resp.raise_for_status()
        return resp.json()
