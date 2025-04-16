"""
Strict MCP protocol types for Python server.
Stub: Replace with imports from @modelcontextprotocol/sdk/python if available.
"""
from pydantic import BaseModel
from typing import List, Dict, Optional

# Example MCP types (replace with actual SDK types)
class ToolRequest(BaseModel):
    tool: str
    input: dict

class Prompt(BaseModel):
    prompt: str
    context: Optional[dict]

class Resource(BaseModel):
    id: str
    type: str
    data: dict

# --- Project & File Resources ---
class Project(BaseModel):
    name: str
    path: str
    # Add other metadata fields as needed

class File(BaseModel):
    name: str
    path: str
    project: str
    # Add other fields as needed

class Document(BaseModel):
    id: str
    name: str
    project: str
    content: Optional[str] = None

# --- Graph Resources ---
class GraphNode(BaseModel):
    id: str
    label: str
    type: str

class GraphEdge(BaseModel):
    source: str
    target: str
    label: Optional[str]

class Graph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# --- Tool Inputs/Outputs ---
class QueryRequest(BaseModel):
    project: str
    query: str

class QueryResult(BaseModel):
    results: List[dict]

class GraphNeighborsRequest(BaseModel):
    project: str
    node_id: str

class UploadDocumentRequest(BaseModel):
    project: str
    name: str
    content: str

class ReindexDocumentRequest(BaseModel):
    project: str
    doc_id: str

class IndexerStatusUpdateRequest(BaseModel):
    projects: List[str]

class AddProjectRequest(BaseModel):
    path: str
    name: str

class DeleteProjectRequest(BaseModel):
    name: str

class ExplainRequest(BaseModel):
    project: str
    query: str
    result: dict

class ChunkSearchResult(BaseModel):
    results: List[dict]

# Add more types as needed for strict typing of all tool requests/responses

# Add more types as per MCP SDK
