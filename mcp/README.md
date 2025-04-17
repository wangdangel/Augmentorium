# MCP Python Server for Augmentorium

This server implements the Model Context Protocol (MCP) for connecting to the Augmentorium RAG server.

## Features
- **Strict typing** using Pydantic types for all tool/resource requests and responses
- **Connects to the RAG server** via REST API at `http://localhost:6655`
- **All tools and resources are exposed via SSE and stdio only**
- **No standard HTTP REST API for tool/resource invocation**
- **LLM/agent friendly:** clear error messages, discoverable schemas, and streaming-first
- **DRY:** Reuses types and functions where possible
- **Only operates within this `mcp/` folder**

## Project Structure
- `mcp_server.py` – Main entry point (SSE endpoints only)
- `stdio_server.py` – Standard IO (stdio) transport for CLI/agent/LLM use
- `types.py` – Strict MCP protocol types
- `rag_client.py` – Async client for RAG server
- `requirements.txt` – Python dependencies

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run the SSE server: `python mcp_server.py` (serves only `/sse/...` endpoints)
3. Run stdio server: `python stdio_server.py` (reads/writes JSON lines)

## SSE Transport
- All tools: `/sse/tools/{tool}/invoke`
- All resources: `/sse/resources`, `/sse/resources/{project}`, etc.
- Each endpoint streams `{ "event": "result", "data": ... }` or `{ "event": "error", ... }`

## Stdio Transport
- Input: `{ "tool": "query", "data": { ... } }` (see `TOOL_MAP` in stdio_server.py)
- Output: `{ "result": ... }` or `{ "error": ... }`
- Full parity with SSE endpoints

## Notes
- No standard HTTP REST API for any tool/resource invocation
- See MCP documentation for protocol details and conventions
- For LLM/agent integration, always use SSE or stdio transports
