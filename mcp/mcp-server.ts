#!/usr/bin/env node

// Augmentorium MCP Server (TypeScript/JavaScript, Stdio Transport)
// Fully ported from Python version: all tool handlers forward to RAG backend via HTTP

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// --- Config ---
const RAG_SERVER_URL = 'http://localhost:6655'; // Change if needed

// --- Server Description ---
// This MCP server provides advanced Retrieval-Augmented Generation (RAG) capabilities, including semantic search, chunk search, graph analysis, and project/document management. Agents and LLMs are strongly encouraged to use the RAG/meta-tools for all code understanding, impact analysis, and cross-modal queries, as these provide the most comprehensive and accurate results.

// --- Tool Schemas (expand as needed) ---
const toolSchemas = [
  {
    name: 'list_projects',
    description: 'List all available projects. This should be called before using the project or vector_database meta-tools to discover project names.\n\nNote: This MCP server supports advanced RAG (Retrieval-Augmented Generation) features. Agents and LLMs are encouraged to use the RAG/meta-tools for all code understanding, impact analysis, and cross-modal queries, as these provide the most comprehensive and accurate results.',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    },
    outputSchema: {
      type: 'object',
      properties: {
        result: { type: 'object' }
      },
      required: ['result']
    }
  },
  {
    name: 'graph',
    description: 'Unified tool for graph operations: fetch the full graph, get neighbors of a node, or search for nodes/edges by substring or property. Use the "action" parameter to select the operation.\n\nThis server provides RAG/meta-tools—agents/LLMs should use these for dependency, impact, and cross-modal analysis.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['get_graph', 'graph_neighbors', 'search_nodes', 'search_edges'],
          description: 'The graph operation to perform.'
        },
        project: { type: 'string', description: 'Project name.' },
        node_id: { type: 'string', description: 'Required for graph_neighbors.' },
        query: { type: 'string', description: 'Substring/property for search.' }
      },
      required: ['action', 'project']
    },
    outputSchema: {
      type: 'object',
      properties: {
        result: { type: 'object' }
      },
      required: ['result']
    }
  },
  {
    name: 'project',
    description: 'Unified tool for project management actions. The FIRST action any LLM should take is list_projects to discover available projects. Actions: list_projects, get_project, add_project, delete_project, list_files, list_documents. Use the action parameter to select the operation.\n\nNote: This server supports RAG/meta-tools for semantic and cross-modal queries—agents/LLMs should use these for deep project analysis.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['list_projects', 'get_project', 'add_project', 'delete_project', 'list_files', 'list_documents'],
          description: 'The project management action to perform.'
        },
        project: { type: 'string', description: 'Project name (required for all except list_projects and add_project).' },
        path: { type: 'string', description: 'Path for add_project.' },
        name: { type: 'string', description: 'Project name for add_project/delete_project.' }
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        result: { type: 'object' }
      },
      required: ['result']
    }
  },
  {
    name: 'vector_database',
    description: 'Unified tool for all vector database operations. Actions: query (semantic search), chunk_search (search document chunks), list_chunks (list all indexed chunks), explain (explain a vector search result), reindex_document (recompute embeddings for a document). Use the action parameter to select the operation.\n\nThis server provides RAG/meta-tools—agents/LLMs should use these for semantic search, similarity matching, and impact analysis.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['query', 'chunk_search', 'list_chunks', 'explain', 'reindex_document'],
          description: 'The vector database action to perform.'
        },
        project: { type: 'string', description: 'Project name (required for all except explain).' },
        query: { type: 'string', description: 'Query string for search.' },
        doc_id: { type: 'string', description: 'Document ID for reindex_document.' },
        result: { type: 'object', description: 'Result object for explain.' }
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        result: { type: 'object' }
      },
      required: ['result']
    }
  },
  { name: 'upload_document', description: 'Upload a new document to the project.\n\nNote: For richer project understanding and semantic search, use the RAG/meta-tools provided by this server.', inputSchema: { type: 'object', properties: { project: { type: 'string' }, name: { type: 'string' }, content: { type: 'string' } }, required: ['project', 'name', 'content'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
];

// --- Tool handler implementation ---
async function callRagApi(method: 'get' | 'post' | 'delete', url: string, data?: any) {
  try {
    const config: any = { method, url, data };
    if (method === 'get' && data) config.params = data;
    const resp = await axios(config);
    return resp.data;
  } catch (error: any) {
    throw new McpError(ErrorCode.InternalError, error.message || 'Backend error');
  }
}

class AugmentoriumMcpServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'augmentorium-mcp-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        }
        // description: 'This MCP server provides advanced Retrieval-Augmented Generation (RAG) capabilities, including semantic search, chunk search, graph analysis, and project/document management. Agents and LLMs are strongly encouraged to use the RAG/meta-tools for all code understanding, impact analysis, and cross-modal queries, as these provide the most comprehensive and accurate results.'
      }
    );

    this.setupToolHandlers();
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', () => process.exit(0));
    process.on('SIGTERM', () => process.exit(0));
  }

  private setupToolHandlers() {
    // ListTools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return { tools: toolSchemas.map(({ name, description, inputSchema, outputSchema }) => ({
        name,
        description,
        inputSchema,
        outputSchema
      })) };
    });

    // CallTool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const args = request.params.arguments || {};
      switch (request.params.name) {
        case 'list_projects': {
          const result = await callRagApi('get', `${RAG_SERVER_URL}/api/projects/`);
          return { content: [{ type: 'json', json: { result } }] };
        }
        case 'graph': {
          if (!args.project || !args.action) throw new McpError(ErrorCode.InvalidRequest, 'Missing project or action');
          switch (args.action) {
            case 'get_graph': {
              const url = `${RAG_SERVER_URL}/api/graph?project=${encodeURIComponent(String(args.project))}`;
              const result = await callRagApi('get', url);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'graph_neighbors': {
              if (!args.node_id) throw new McpError(ErrorCode.InvalidRequest, 'Missing node_id');
              const url = `${RAG_SERVER_URL}/api/graph/neighbors?project=${encodeURIComponent(String(args.project))}&node_id=${encodeURIComponent(String(args.node_id))}`;
              const result = await callRagApi('get', url);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'search_nodes': {
              if (!args.query) throw new McpError(ErrorCode.InvalidRequest, 'Missing query');
              const url = `${RAG_SERVER_URL}/api/graph/search_nodes?project=${encodeURIComponent(String(args.project))}&query=${encodeURIComponent(String(args.query))}`;
              const result = await callRagApi('get', url);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'search_edges': {
              if (!args.query) throw new McpError(ErrorCode.InvalidRequest, 'Missing query');
              const url = `${RAG_SERVER_URL}/api/graph/search_edges?project=${encodeURIComponent(String(args.project))}&query=${encodeURIComponent(String(args.query))}`;
              const result = await callRagApi('get', url);
              return { content: [{ type: 'json', json: { result } }] };
            }
            default:
              throw new McpError(ErrorCode.InvalidRequest, `Unknown graph action: ${args.action}`);
          }
        }
        case 'project': {
          if (!args.action) throw new McpError(ErrorCode.InvalidRequest, 'Missing action');
          switch (args.action) {
            case 'list_projects': {
              const result = await callRagApi('get', `${RAG_SERVER_URL}/api/projects/`);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'get_project': {
              if (!args.project) throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
              const result = await callRagApi('get', `${RAG_SERVER_URL}/api/projects/${args.project}`);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'add_project': {
              if (!args.path || !args.name) throw new McpError(ErrorCode.InvalidRequest, 'Missing path or name');
              const result = await callRagApi('post', `${RAG_SERVER_URL}/api/projects/`, { path: args.path, name: args.name });
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'delete_project': {
              if (!args.name) throw new McpError(ErrorCode.InvalidRequest, 'Missing name');
              const result = await callRagApi('delete', `${RAG_SERVER_URL}/api/projects/${args.name}`);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'list_files': {
              if (!args.project) throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
              const url = `${RAG_SERVER_URL}/api/files/?project=${encodeURIComponent(String(args.project))}`;
              const result = await callRagApi('get', url);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'list_documents': {
              if (!args.project) throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
              const url = `${RAG_SERVER_URL}/api/documents/?project=${encodeURIComponent(String(args.project))}`;
              const result = await callRagApi('get', url);
              return { content: [{ type: 'json', json: { result } }] };
            }
            default:
              throw new McpError(ErrorCode.InvalidRequest, `Unknown project action: ${args.action}`);
          }
        }
        case 'vector_database': {
          if (!args.action) throw new McpError(ErrorCode.InvalidRequest, 'Missing action');
          switch (args.action) {
            case 'query': {
              if (!args.project || !args.query) throw new McpError(ErrorCode.InvalidRequest, 'Missing project or query');
              const result = await callRagApi('post', `${RAG_SERVER_URL}/api/query/`, { project: args.project, query: args.query });
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'chunk_search': {
              if (!args.project || !args.query) throw new McpError(ErrorCode.InvalidRequest, 'Missing project or query');
              const result = await callRagApi('post', `${RAG_SERVER_URL}/api/chunks/search`, { project: args.project, query: args.query });
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'list_chunks': {
              if (!args.project) throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
              const result = await callRagApi('get', `${RAG_SERVER_URL}/api/chunks/?project=${encodeURIComponent(String(args.project))}`);
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'explain': {
              if (!args.project || !args.query || !args.result) throw new McpError(ErrorCode.InvalidRequest, 'Missing project, query, or result');
              const result = await callRagApi('post', `${RAG_SERVER_URL}/api/explain/`, { project: args.project, query: args.query, result: args.result });
              return { content: [{ type: 'json', json: { result } }] };
            }
            case 'reindex_document': {
              if (!args.project || !args.doc_id) throw new McpError(ErrorCode.InvalidRequest, 'Missing project or doc_id');
              const result = await callRagApi('post', `${RAG_SERVER_URL}/api/documents/${args.doc_id}/reindex`, { project: args.project });
              return { content: [{ type: 'json', json: { result } }] };
            }
            default:
              throw new McpError(ErrorCode.InvalidRequest, `Unknown vector database action: ${args.action}`);
          }
        }
        case 'upload_document': {
          if (!args.project || !args.name || !args.content) throw new McpError(ErrorCode.InvalidRequest, 'Missing project, name, or content');
          return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/documents/`, { project: args.project, name: args.name, content: args.content }) }] };
        }
        default:
          throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

export async function startMcpServer() {
  try {
    const serverInstance = new AugmentoriumMcpServer();
    await serverInstance.run();
  } catch (error) {
    console.error('Failed to start Augmentorium MCP server:', error);
    process.exit(1);
  }
}

startMcpServer();

export { AugmentoriumMcpServer };

// PATCH: Use ErrorCode.InvalidRequest for invalid arguments (universal fallback)
// If your SDK requires ErrorCode.InvalidParams or another, change here.
