#!/usr/bin/env node
// Augmentorium MCP Server (TypeScript/JavaScript, Stdio Transport)
// Fully ported from Python version: all tool handlers forward to RAG backend via HTTP
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ErrorCode, ListToolsRequestSchema, McpError, } from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
// --- Config ---
const RAG_SERVER_URL = 'http://localhost:6655'; // Change if needed
// --- Tool Schemas (expand as needed) ---
const toolSchemas = [
    {
        name: 'query',
        description: 'Run a query against the project knowledge base.',
        inputSchema: {
            type: 'object',
            properties: {
                project: { type: 'string' },
                query: { type: 'string' }
            },
            required: ['project', 'query']
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
        name: 'chunk_search',
        description: 'Search document chunks in the project.',
        inputSchema: {
            type: 'object',
            properties: {
                project: { type: 'string' },
                query: { type: 'string' }
            },
            required: ['project', 'query']
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
        name: 'graph_neighbors',
        description: 'Get neighbors of a node in the project graph.',
        inputSchema: {
            type: 'object',
            properties: {
                project: { type: 'string' },
                node_id: { type: 'string' }
            },
            required: ['project', 'node_id']
        },
        outputSchema: {
            type: 'object',
            properties: {
                result: { type: 'object' }
            },
            required: ['result']
        }
    },
    { name: 'upload_document', description: 'Upload a new document to the project.', inputSchema: { type: 'object', properties: { project: { type: 'string' }, name: { type: 'string' }, content: { type: 'string' } }, required: ['project', 'name', 'content'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'explain', description: 'Explain a query result.', inputSchema: { type: 'object', properties: { project: { type: 'string' }, query: { type: 'string' }, result: { type: 'object' } }, required: ['project', 'query', 'result'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'add_project', description: 'Add a new project.', inputSchema: { type: 'object', properties: { path: { type: 'string' }, name: { type: 'string' } }, required: ['path', 'name'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'delete_project', description: 'Delete a project.', inputSchema: { type: 'object', properties: { name: { type: 'string' } }, required: ['name'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'reindex_document', description: 'Reindex a document in the project.', inputSchema: { type: 'object', properties: { project: { type: 'string' }, doc_id: { type: 'string' } }, required: ['project', 'doc_id'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'update_indexer_status', description: 'Update the indexer status for projects.', inputSchema: { type: 'object', properties: { projects: { type: 'array', items: { type: 'string' } } }, required: ['projects'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'clear_query_cache', description: 'Clear the query cache for a project.', inputSchema: { type: 'object', properties: { project: { type: 'string' } }, required: ['project'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'clear_general_cache', description: 'Clear the general cache for a project.', inputSchema: { type: 'object', properties: { project: { type: 'string' } }, required: ['project'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'list_projects', description: 'List all available projects.', inputSchema: { type: 'object', properties: {}, required: [] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'get_project', description: 'Get details about a project.', inputSchema: { type: 'object', properties: { project: { type: 'string' } }, required: ['project'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'list_files', description: 'List all files in a project.', inputSchema: { type: 'object', properties: { project: { type: 'string' } }, required: ['project'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'list_documents', description: 'List all documents in a project.', inputSchema: { type: 'object', properties: { project: { type: 'string' } }, required: ['project'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
    { name: 'get_graph', description: 'Get the graph for a project.', inputSchema: { type: 'object', properties: { project: { type: 'string' } }, required: ['project'] }, outputSchema: { type: 'object', properties: { result: { type: 'object' } }, required: ['result'] } },
];
// --- Tool handler implementation ---
async function callRagApi(method, url, data) {
    try {
        const config = { method, url, data };
        if (method === 'get' && data)
            config.params = data;
        const resp = await axios(config);
        return resp.data;
    }
    catch (error) {
        throw new McpError(ErrorCode.InternalError, error.message || 'Backend error');
    }
}
class AugmentoriumMcpServer {
    constructor() {
        this.server = new Server({
            name: 'augmentorium-mcp-server',
            version: '0.1.0',
        }, {
            capabilities: {
                resources: {},
                tools: {},
            },
        });
        this.setupToolHandlers();
        this.server.onerror = (error) => console.error('[MCP Error]', error);
        process.on('SIGINT', () => process.exit(0));
        process.on('SIGTERM', () => process.exit(0));
    }
    setupToolHandlers() {
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
                case 'query':
                    if (!args.project || !args.query)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project or query');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/query/`, { project: args.project, query: args.query }) }] };
                case 'chunk_search':
                    if (!args.project || !args.query)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project or query');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/chunks/search`, { project: args.project, query: args.query }) }] };
                case 'graph_neighbors':
                    if (!args.project || !args.node_id)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project or node_id');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/graph/neighbors/`, { project: args.project, node_id: args.node_id }) }] };
                case 'upload_document':
                    if (!args.project || !args.name || !args.content)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project, name, or content');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/documents/upload`, { project: args.project, name: args.name, content: args.content }) }] };
                case 'explain':
                    if (!args.project || !args.query || !args.result)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project, query, or result');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/explain/`, { project: args.project, query: args.query, result: args.result }) }] };
                case 'add_project':
                    if (!args.path || !args.name)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing path or name');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/projects/`, { path: args.path, name: args.name }) }] };
                case 'delete_project':
                    if (!args.name)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing name');
                    return { content: [{ type: 'json', json: await callRagApi('delete', `${RAG_SERVER_URL}/api/projects/${args.name}`) }] };
                case 'reindex_document':
                    if (!args.project || !args.doc_id)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project or doc_id');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/documents/${args.doc_id}/reindex`, { project: args.project }) }] };
                case 'update_indexer_status':
                    if (!args.projects)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing projects');
                    return { content: [{ type: 'json', json: await callRagApi('post', `${RAG_SERVER_URL}/api/indexer/status`, { projects: args.projects }) }] };
                case 'clear_query_cache':
                    if (!args.project)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                    return { content: [{ type: 'json', json: await callRagApi('delete', `${RAG_SERVER_URL}/api/query/cache`, { project: args.project }) }] };
                case 'clear_general_cache':
                    if (!args.project)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                    return { content: [{ type: 'json', json: await callRagApi('delete', `${RAG_SERVER_URL}/api/cache/`, { project: args.project }) }] };
                case 'list_projects':
                    return { content: [{ type: 'json', json: await callRagApi('get', `${RAG_SERVER_URL}/api/projects/`) }] };
                case 'get_project':
                    if (!args.project)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                    return { content: [{ type: 'json', json: await callRagApi('get', `${RAG_SERVER_URL}/api/projects/${args.project}`) }] };
                case 'list_files':
                    if (!args.project)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                    return { content: [{ type: 'json', json: await callRagApi('get', `${RAG_SERVER_URL}/api/files/`, { project: args.project }) }] };
                case 'list_documents':
                    if (!args.project)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                    return { content: [{ type: 'json', json: await callRagApi('get', `${RAG_SERVER_URL}/api/documents/`, { project: args.project }) }] };
                case 'get_graph':
                    if (!args.project)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                    return { content: [{ type: 'json', json: await callRagApi('get', `${RAG_SERVER_URL}/api/graph/`, { project: args.project }) }] };
                default:
                    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
            }
        });
    }
    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.log('Augmentorium MCP server running on stdio');
    }
}
export async function startMcpServer() {
    try {
        const serverInstance = new AugmentoriumMcpServer();
        await serverInstance.run();
    }
    catch (error) {
        console.error('Failed to start Augmentorium MCP server:', error);
        process.exit(1);
    }
}
if (require.main === module) {
    startMcpServer();
}
export { AugmentoriumMcpServer };
// PATCH: Use ErrorCode.InvalidRequest for invalid arguments (universal fallback)
// If your SDK requires ErrorCode.InvalidParams or another, change here.
