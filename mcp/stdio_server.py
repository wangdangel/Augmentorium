"""
MCP stdio transport server for Augmentorium.
Reads JSON requests from stdin, writes JSON responses to stdout.
Logs all requests and responses for debugging.
"""
import sys
import json
import logging
from mcp_server import app, TOOLS_METADATA
from fastapi.encoders import jsonable_encoder
from types import SimpleNamespace
from typing import Any

logging.basicConfig(level=logging.INFO, format='[STDIO] %(message)s')

# Simulate FastAPI endpoint calls
import rag_client
import mcp_types as types
import asyncio

# Map tool/resource names to functions (full parity with SSE endpoints)
TOOL_MAP = {
    "query": lambda data: rag_client.run_query(data["project"], data["query"]),
    "chunk_search": lambda data: rag_client.search_chunks(data["project"], data["query"]),
    "graph_neighbors": lambda data: rag_client.fetch_graph_neighbors(data["project"], data["node_id"]),
    "upload_document": lambda data: rag_client.upload_document(data["project"], data["name"], data["content"]),
    "explain": lambda data: rag_client.explain(data["project"], data["query"], data["result"]),
    "add_project": lambda data: rag_client.add_project(data["path"], data["name"]),
    "delete_project": lambda data: rag_client.delete_project(data["name"]),
    "clear_query_cache": lambda data: rag_client.clear_query_cache(data["project"]),
    "clear_general_cache": lambda data: rag_client.clear_general_cache(data["project"]),
    "reindex_document": lambda data: rag_client.reindex_document(data["project"], data["doc_id"]),
    "update_indexer_status": lambda data: rag_client.update_indexer_status(data["projects"]),
    # Resource endpoints
    "list_projects": lambda data: rag_client.fetch_projects(),
    "get_project": lambda data: rag_client.fetch_project(data["project"]),
    "list_files": lambda data: rag_client.fetch_files(data["project"]),
    "list_documents": lambda data: rag_client.fetch_documents(data["project"]),
    "get_graph": lambda data: rag_client.fetch_graph(data["project"]),
}

async def handle_request(request: dict) -> dict:
    logging.info(f"Received: {request}")
    # JSON-RPC compatibility
    if "method" in request:
        method = request["method"]
        req_id = request.get("id")
        # Handle MCP Inspector handshake methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "serverInfo": {
                        "name": "Augmentorium MCP Server",
                        "version": "0.1.0",
                        "status": "ok"
                    },
                    "capabilities": {
                        "tools": True,
                        "resources": False,
                        "prompts": False,
                        "sse": True,
                        "stdio": True
                    }
                }
            }
            logging.info(f"Responding: {response}")
            return response
        elif method == "listTools":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": [tool.dict() for tool in TOOLS_METADATA]
            }
            logging.info(f"Responding: {response}")
            # Also print the response to stdout for debugging
            print(json.dumps(response), flush=True)
            return response
        # Add more JSON-RPC methods as needed (e.g., invoke, shutdown)
        else:
            response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' not implemented"}}
            logging.info(f"Responding: {response}")
            return response
    # Legacy/tool invocation mode
    tool = request.get("tool")
    data = request.get("data", {})
    if not tool or tool not in TOOL_MAP:
        response = {"error": f"Unknown or missing tool: {tool}"}
        logging.info(f"Responding: {response}")
        return response
    try:
        result = await TOOL_MAP[tool](data)
        response = {"result": result}
    except Exception as e:
        response = {"error": str(e)}
    logging.info(f"Responding: {response}")
    return response

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except Exception as e:
            print(json.dumps({"error": f"Invalid JSON: {e}"}), flush=True)
            continue
        response = asyncio.run(handle_request(request))
        print(json.dumps(jsonable_encoder(response)), flush=True)

if __name__ == "__main__":
    main()
