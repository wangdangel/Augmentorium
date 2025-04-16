"""
Entry point for the MCP Python server for Augmentorium.
Strictly typed, MCP-compliant, supports stdio and SSE.
"""
from fastapi import FastAPI, Request, Body, APIRouter
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from sse_starlette.sse import EventSourceResponse
import httpx
from typing import Any, List, Dict
import mcp_types as types
from rag_client import (
    fetch_tools, fetch_tool,
    fetch_prompts, fetch_prompt,
    fetch_resources, fetch_resource,
    fetch_projects, fetch_files, fetch_documents,
    fetch_graph, fetch_graph_neighbors, run_query, upload_document, explain,
    fetch_stats, fetch_indexer_status, search_chunks,
    clear_query_cache, clear_general_cache, update_indexer_status
)
import asyncio

app = FastAPI(title="Augmentorium MCP Server", version="0.1.0")

# TODO: Load MCP resources, tools, prompts, etc. from RAG server
# TODO: Implement stdio and SSE transports
# TODO: Strict typing everywhere

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# --- MCP Resource Endpoints ---
@app.get("/resources", response_model=List[types.Project])
async def list_projects():
    """List all available projects. LLMs and clients should start by selecting a project name."""
    projects = await fetch_projects()
    return [types.Project(**p) for p in projects]

@app.get("/resources/{project}", response_model=types.Project)
async def get_project(project: str):
    projects = await fetch_projects()
    match = next((p for p in projects if p['name'] == project), None)
    if not match:
        return JSONResponse(status_code=404, content={"detail": "Project not found"})
    return types.Project(**match)

@app.get("/resources/{project}/files", response_model=List[types.File])
async def list_files(project: str, max_files: int = 20):
    files = await fetch_files(project, max_files)
    return [types.File(**f) for f in files]

@app.get("/resources/{project}/documents", response_model=List[types.Document])
async def list_documents(project: str):
    docs = await fetch_documents(project)
    return [types.Document(**d) for d in docs]

@app.get("/resources/{project}/graph", response_model=types.Graph)
async def get_graph(project: str):
    g = await fetch_graph(project)
    return types.Graph(**g)

# --- MCP Tool Listing ---
class ToolInfo(types.BaseModel):
    name: str
    description: str
    sse_url: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]

TOOLS_METADATA = [
    ToolInfo(
        name="query",
        description="Run a query against the project knowledge base.",
        sse_url="/sse/tools/query/invoke",
        input_schema={"project": "string", "query": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="chunk_search",
        description="Search document chunks in the project.",
        sse_url="/sse/tools/chunk_search/invoke",
        input_schema={"project": "string", "query": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="graph_neighbors",
        description="Get neighbors of a node in the project graph.",
        sse_url="/sse/tools/graph_neighbors/invoke",
        input_schema={"project": "string", "node_id": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="upload_document",
        description="Upload a new document to the project.",
        sse_url="/sse/tools/upload_document/invoke",
        input_schema={"project": "string", "name": "string", "content": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="explain",
        description="Explain a query result.",
        sse_url="/sse/tools/explain/invoke",
        input_schema={"project": "string", "query": "string", "result": "object"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="add_project",
        description="Add a new project.",
        sse_url="/sse/tools/add_project/invoke",
        input_schema={"path": "string", "name": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="delete_project",
        description="Delete a project.",
        sse_url="/sse/tools/delete_project/invoke",
        input_schema={"name": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="reindex_document",
        description="Reindex a document in the project.",
        sse_url="/sse/tools/reindex_document/invoke",
        input_schema={"project": "string", "doc_id": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="update_indexer_status",
        description="Update the indexer status for projects.",
        sse_url="/sse/tools/update_indexer_status/invoke",
        input_schema={"projects": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="clear_query_cache",
        description="Clear the query cache for a project.",
        sse_url="/sse/tools/clear_query_cache/invoke",
        input_schema={"project": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="clear_general_cache",
        description="Clear the general cache for a project.",
        sse_url="/sse/tools/clear_general_cache/invoke",
        input_schema={"project": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="list_projects",
        description="List all available projects.",
        sse_url="/sse/tools/list_projects/invoke",
        input_schema={},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="get_project",
        description="Get details about a project.",
        sse_url="/sse/tools/get_project/invoke",
        input_schema={"project": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="list_files",
        description="List all files in a project.",
        sse_url="/sse/tools/list_files/invoke",
        input_schema={"project": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="list_documents",
        description="List all documents in a project.",
        sse_url="/sse/tools/list_documents/invoke",
        input_schema={"project": "string"},
        output_schema={"result": "object"}
    ),
    ToolInfo(
        name="get_graph",
        description="Get the graph for a project.",
        sse_url="/sse/tools/get_graph/invoke",
        input_schema={"project": "string"},
        output_schema={"result": "object"}
    ),
]

@app.get("/sse/tools", response_class=EventSourceResponse)
async def sse_list_tools(request: Request):
    async def event_generator():
        # Yield the tool metadata as an SSE event
        yield {"event": "tools", "data": [tool.dict() for tool in TOOLS_METADATA]}
        # Keep connection alive with periodic pings
        import asyncio
        while True:
            await asyncio.sleep(15)
            yield {"event": "ping", "data": "pong"}
    return EventSourceResponse(event_generator())

@app.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    return TOOLS_METADATA

# --- SSE Endpoints for all tools ---
@app.get("/sse", response_class=EventSourceResponse)
async def sse_ping(request: Request):
    async def event_generator():
        # Send initial server info event
        yield {"event": "ready", "data": {"name": "Augmentorium MCP Server", "version": "0.1.0", "status": "ok"}}
        # Send list of tools for negotiation/handshake
        tools = [
            "query",
            "chunk_search",
            "graph_neighbors",
            "upload_document",
            "explain",
            "add_project",
            "delete_project",
            "reindex_document",
            "update_indexer_status",
            "clear_query_cache",
            "clear_general_cache",
            "list_projects",
            "get_project",
            "list_files",
            "list_documents",
            "get_graph"
        ]
        yield {"event": "tools", "data": tools}
        # Keep connection alive with periodic pings
        while True:
            await asyncio.sleep(15)
            yield {"event": "ping", "data": "pong"}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/query/invoke")
async def sse_invoke_query(project: str, query: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to run a query. Please specify a valid project name."}
            return
        result = await run_query(project, query)
        yield {"event": "result", "data": result}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/chunk_search/invoke")
async def sse_invoke_chunk_search(project: str, query: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to run a chunk search. Please specify a valid project name."}
            return
        result = await search_chunks(project, query)
        yield {"event": "result", "data": result}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/graph_neighbors/invoke")
async def sse_invoke_graph_neighbors(project: str, node_id: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to get graph neighbors. Please specify a valid project name."}
            return
        result = await fetch_graph_neighbors(project, node_id)
        yield {"event": "result", "data": result}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/upload_document/invoke")
async def sse_invoke_upload_document(project: str, name: str, content: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to upload a document. Please specify a valid project name."}
            return
        result = await upload_document(project, name, content)
        yield {"event": "result", "data": result}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/explain/invoke")
async def sse_invoke_explain(project: str, query: str, result: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to explain a result. Please specify a valid project name."}
            return
        result_obj = await explain(project, query, result)
        yield {"event": "result", "data": result_obj}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/reindex_document/invoke")
async def sse_invoke_reindex_document(project: str, doc_id: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to reindex a document. Please specify a valid project name."}
            return
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://localhost:6655/api/documents/{doc_id}/reindex", json={"project": project})
            resp.raise_for_status()
            yield {"event": "result", "data": resp.json()}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/clear_query_cache/invoke")
async def sse_invoke_clear_query_cache(project: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to clear the query cache. Please specify a valid project name."}
            return
        result = await clear_query_cache(project)
        yield {"event": "result", "data": result}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/clear_general_cache/invoke")
async def sse_invoke_clear_general_cache(project: str, request: Request):
    async def event_generator():
        if not project:
            yield {"event": "error", "data": "A project name is required to clear the general cache. Please specify a valid project name."}
            return
        result = await clear_general_cache(project)
        yield {"event": "result", "data": result}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/add_project/invoke")
async def sse_invoke_add_project(path: str, name: str, request: Request):
    async def event_generator():
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://localhost:6655/api/projects/", json={"path": path, "name": name})
            resp.raise_for_status()
            yield {"event": "result", "data": resp.json()}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/delete_project/invoke")
async def sse_invoke_delete_project(name: str, request: Request):
    async def event_generator():
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"http://localhost:6655/api/projects/{name}")
            resp.raise_for_status()
            yield {"event": "result", "data": resp.json()}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/update_indexer_status/invoke")
async def sse_invoke_update_indexer_status(projects: str, request: Request):
    async def event_generator():
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://localhost:6655/api/indexer/status", json={"projects": projects})
            resp.raise_for_status()
            yield {"event": "result", "data": resp.json()}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/list_projects/invoke")
async def sse_invoke_list_projects(request: Request):
    async def event_generator():
        projects = await fetch_projects()
        yield {"event": "result", "data": projects}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/get_project/invoke")
async def sse_invoke_get_project(project: str, request: Request):
    async def event_generator():
        details = await fetch_project(project)
        yield {"event": "result", "data": details}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/list_files/invoke")
async def sse_invoke_list_files(project: str, request: Request):
    async def event_generator():
        files = await fetch_files(project)
        yield {"event": "result", "data": files}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/list_documents/invoke")
async def sse_invoke_list_documents(project: str, request: Request):
    async def event_generator():
        docs = await fetch_documents(project)
        yield {"event": "result", "data": docs}
    return EventSourceResponse(event_generator())

@app.get("/sse/tools/get_graph/invoke")
async def sse_invoke_get_graph(project: str, request: Request):
    async def event_generator():
        graph = await fetch_graph(project)
        yield {"event": "result", "data": graph}
    return EventSourceResponse(event_generator())

# --- CATCH-ALL FOR NON-TOOL ENDPOINTS ---
@app.get("/sse/resources{full_path:path}")
async def resource_not_supported(full_path: str):
    return PlainTextResponse("Resource endpoints are not supported on this server. Only tools are available.", status_code=404)

@app.get("/sse/prompts{full_path:path}")
async def prompt_not_supported(full_path: str):
    return PlainTextResponse("Prompt endpoints are not supported on this server. Only tools are available.", status_code=404)

# --- MCP Root Endpoint ---
@app.get("/", response_model=dict)
async def root():
    return {
        "name": "Augmentorium MCP Server",
        "version": "0.1.0",
        "status": "ok",
        "sse_tools_base": "/sse/tools",
        "transports": ["sse", "stdio"]
    }

@app.get("/mcp_root")
def mcp_root():
    return {
        "name": "Augmentorium MCP Server",
        "version": "0.1.0",
        "resources": "/resources",
        "tools": "/tools",
        "sse": "/sse/"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=6657, reload=True)
