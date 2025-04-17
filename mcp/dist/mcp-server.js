#!/usr/bin/env node
process.stdin.on('data', (chunk) => {
    console.log('[RAW STDIN]', chunk.toString());
});
// Augmentorium MCP Server (TypeScript/JavaScript, Stdio Transport)
// Fully ported from Python version: all tool handlers forward to RAG backend via HTTP
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ErrorCode, ListToolsRequestSchema, McpError, } from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
// --- Config ---
const RAG_SERVER_URL = 'http://localhost:6655'; // Change if needed
// --- Server Description ---
// This MCP server provides advanced Retrieval-Augmented Generation (RAG) capabilities, including semantic search, chunk search, graph analysis, and project/document management. Agents and LLMs are strongly encouraged to use the RAG/meta-tools for all code understanding, impact analysis, and cross-modal queries, as these provide the most comprehensive and accurate results.
// --- Tool Schemas (expand as needed) ---
const toolSchemas = [
    {
        name: 'list_projects',
        description: 'List all available projects. Use this to discover valid project names before using other project tools.',
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
        description: 'Unified tool for graph operations: fetch the full graph, get neighbors of a node, or search for nodes/edges by substring or property. Use the "action" parameter to select the operation.\n\nIMPORTANT: Always pass the project name using the \'project\' field (not \'name\').',
        inputSchema: {
            type: 'object',
            properties: {
                action: {
                    type: 'string',
                    enum: ['get_graph', 'graph_neighbors', 'search_nodes', 'search_edges'],
                    description: 'The graph operation to perform.'
                },
                project: { type: 'string', description: 'Project name (REQUIRED, use the \'project\' field, not \'name\').' },
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
        description: `Unified tool for project management actions.\nThe FIRST action any LLM should take is list_projects to discover available projects.\nActions:\n- list_projects: List all projects (no arguments required).\n- get_project: Retrieve a single project's metadata. Pass the project name in the 'project' field.\n- add_project: Add a new project. Pass the project name in the 'name' field and path in the 'path' field.\n- delete_project: Delete a project. Pass the project name in the 'name' field.\n- list_files: List files for a project. Pass the project name in the 'project' field.\n- list_documents: List documents for a project. Pass the project name in the 'project' field.\n\nIMPORTANT: For all actions except add_project and delete_project, pass the project name using the 'project' field (not 'name').`,
        inputSchema: {
            type: 'object',
            properties: {
                action: {
                    type: 'string',
                    enum: ['list_projects', 'get_project', 'add_project', 'delete_project', 'list_files', 'list_documents'],
                    description: 'The project management action to perform.'
                },
                project: { type: 'string', description: "Project name (REQUIRED for get_project, list_files, list_documents. DO NOT use 'name' for these actions)." },
                path: { type: 'string', description: 'Path for add_project.' },
                name: { type: 'string', description: "Project name for add_project/delete_project ONLY. DO NOT use for get_project, list_files, or list_documents." }
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
        description: 'Unified tool for all vector database operations. Actions: query (semantic search), chunk_search (search document chunks), list_chunks (list all indexed chunks), explain (explain a vector search result), reindex_document (recompute embeddings for a document). Use the action parameter to select the operation.\n\nIMPORTANT: Always pass the project name using the \'project\' field (not \'name\').',
        inputSchema: {
            type: 'object',
            properties: {
                action: {
                    type: 'string',
                    enum: ['query', 'chunk_search', 'list_chunks', 'explain', 'reindex_document'],
                    description: 'The vector database action to perform.'
                },
                project: { type: 'string', description: "Project name (REQUIRED for all except explain. Use the 'project' field, not 'name')." },
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
    {
        name: 'upload_document',
        description: 'Upload a new document to the project.\n\nNote: For richer project understanding and semantic search, use the RAG/meta-tools provided by this server. Always pass the project name using the \'project\' field (not \'name\').',
        inputSchema: {
            type: 'object',
            properties: {
                project: { type: 'string', description: "Project name (REQUIRED, use the 'project' field, not 'name')." },
                name: { type: 'string', description: 'Document name.' },
                content: { type: 'string', description: 'Document content.' }
            },
            required: ['project', 'name', 'content']
        },
        outputSchema: {
            type: 'object',
            properties: {
                result: { type: 'object' }
            },
            required: ['result']
        }
    },
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
function wrapResultAsText(result) {
    return { content: [{ type: 'text', text: JSON.stringify(result) }] };
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
            }
            // description: 'This MCP server provides advanced Retrieval-Augmented Generation (RAG) capabilities, including semantic search, chunk search, graph analysis, and project/document management. Agents and LLMs are strongly encouraged to use the RAG/meta-tools for all code understanding, impact analysis, and cross-modal queries, as these provide the most comprehensive and accurate results.'
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
                case 'list_projects': {
                    const result = await callRagApi('get', `${RAG_SERVER_URL}/api/projects/`);
                    return wrapResultAsText({ result });
                }
                case 'graph': {
                    if (!args.project || !args.action)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project or action');
                    switch (args.action) {
                        case 'get_graph': {
                            const url = `${RAG_SERVER_URL}/api/graph?project=${encodeURIComponent(String(args.project))}`;
                            const result = await callRagApi('get', url);
                            return wrapResultAsText({ result });
                        }
                        case 'graph_neighbors': {
                            if (!args.node_id)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing node_id');
                            const url = `${RAG_SERVER_URL}/api/graph/neighbors?project=${encodeURIComponent(String(args.project))}&node_id=${encodeURIComponent(String(args.node_id))}`;
                            const result = await callRagApi('get', url);
                            return wrapResultAsText({ result });
                        }
                        case 'search_nodes': {
                            if (!args.query)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing query');
                            const url = `${RAG_SERVER_URL}/api/graph/search_nodes?project=${encodeURIComponent(String(args.project))}&query=${encodeURIComponent(String(args.query))}`;
                            const result = await callRagApi('get', url);
                            return wrapResultAsText({ result });
                        }
                        case 'search_edges': {
                            if (!args.query)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing query');
                            const url = `${RAG_SERVER_URL}/api/graph/search_edges?project=${encodeURIComponent(String(args.project))}&query=${encodeURIComponent(String(args.query))}`;
                            const result = await callRagApi('get', url);
                            return wrapResultAsText({ result });
                        }
                        default:
                            throw new McpError(ErrorCode.InvalidRequest, `Unknown graph action: ${args.action}`);
                    }
                }
                case 'project': {
                    if (!args.action)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing action');
                    switch (args.action) {
                        case 'list_projects': {
                            const result = await callRagApi('get', `${RAG_SERVER_URL}/api/projects/`);
                            return wrapResultAsText({ result });
                        }
                        case 'get_project': {
                            console.log('[DEBUG] get_project full args:', args);
                            // Try to extract the project name robustly
                            let projectName = (typeof args.project === 'string' && args.project)
                                || (typeof args.name === 'string' && args.name);
                            if (!projectName && args.arguments && typeof args.arguments === 'object') {
                                const argObj = args.arguments;
                                if (typeof argObj.project === 'string') {
                                    projectName = argObj.project;
                                }
                                else if (typeof argObj.name === 'string') {
                                    projectName = argObj.name;
                                }
                            }
                            if (typeof projectName !== 'string') {
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                            }
                            const url = `${RAG_SERVER_URL}/api/projects/${encodeURIComponent(projectName)}`;
                            console.log('[DEBUG] get_project URL:', url);
                            const result = await callRagApi('get', url);
                            console.log('[DEBUG] get_project backend result:', result);
                            return wrapResultAsText({ result });
                        }
                        case 'add_project': {
                            if (!args.path || !args.name)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing path or name');
                            const result = await callRagApi('post', `${RAG_SERVER_URL}/api/projects/`, { path: args.path, name: args.name });
                            return wrapResultAsText({ result });
                        }
                        case 'delete_project': {
                            if (!args.name)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing name');
                            const result = await callRagApi('delete', `${RAG_SERVER_URL}/api/projects/${args.name}`);
                            return wrapResultAsText({ result });
                        }
                        case 'list_files': {
                            if (!args.project)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                            const url = `${RAG_SERVER_URL}/api/files/?project=${encodeURIComponent(String(args.project))}`;
                            const result = await callRagApi('get', url);
                            return wrapResultAsText({ result });
                        }
                        case 'list_documents': {
                            if (!args.project)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                            const url = `${RAG_SERVER_URL}/api/documents/?project=${encodeURIComponent(String(args.project))}`;
                            const result = await callRagApi('get', url);
                            return wrapResultAsText({ result });
                        }
                        default:
                            throw new McpError(ErrorCode.InvalidRequest, `Unknown project action: ${args.action}`);
                    }
                }
                case 'vector_database': {
                    if (!args.action)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing action');
                    switch (args.action) {
                        case 'query': {
                            if (!args.project || !args.query)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project or query');
                            const result = await callRagApi('post', `${RAG_SERVER_URL}/api/query/`, { project: args.project, query: args.query });
                            return wrapResultAsText({ result });
                        }
                        case 'chunk_search': {
                            if (!args.project || !args.query)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project or query');
                            const result = await callRagApi('post', `${RAG_SERVER_URL}/api/chunks/search`, { project: args.project, query: args.query });
                            return wrapResultAsText({ result });
                        }
                        case 'list_chunks': {
                            if (!args.project)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project');
                            const result = await callRagApi('get', `${RAG_SERVER_URL}/api/chunks/?project=${encodeURIComponent(String(args.project))}`);
                            return wrapResultAsText({ result });
                        }
                        case 'explain': {
                            if (!args.project || !args.query || !args.result)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project, query, or result');
                            const result = await callRagApi('post', `${RAG_SERVER_URL}/api/explain/`, { project: args.project, query: args.query, result: args.result });
                            return wrapResultAsText({ result });
                        }
                        case 'reindex_document': {
                            if (!args.project || !args.doc_id)
                                throw new McpError(ErrorCode.InvalidRequest, 'Missing project or doc_id');
                            const result = await callRagApi('post', `${RAG_SERVER_URL}/api/documents/${args.doc_id}/reindex`, { project: args.project });
                            return wrapResultAsText({ result });
                        }
                        default:
                            throw new McpError(ErrorCode.InvalidRequest, `Unknown vector database action: ${args.action}`);
                    }
                }
                case 'upload_document': {
                    if (!args.project || !args.name || !args.content)
                        throw new McpError(ErrorCode.InvalidRequest, 'Missing project, name, or content');
                    const result = await callRagApi('post', `${RAG_SERVER_URL}/api/documents/`, { project: args.project, name: args.name, content: args.content });
                    return wrapResultAsText(result);
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
    }
    catch (error) {
        console.error('Failed to start Augmentorium MCP server:', error);
        process.exit(1);
    }
}
// --- Simple CLI mode for manual testing (robust for ESM/CommonJS) ---
if (process.argv.length > 2) {
    // Usage: node dist/mcp-server.js <tool> <action> <project>
    const [, , tool, action, project] = process.argv;
    (async () => {
        if (tool === 'project' && action && project) {
            const args = { action, project };
            const url = `${RAG_SERVER_URL}/api/projects/${encodeURIComponent(project)}`;
            console.log('[CLI MODE] get_project URL:', url);
            const result = await callRagApi('get', url);
            console.log('[CLI MODE] Result:', result);
        }
        else {
            console.error('Usage: node dist/mcp-server.js project get_project <project_name>');
            process.exit(1);
        }
        process.exit(0);
    })();
}
startMcpServer();
export { AugmentoriumMcpServer };
// PATCH: Use ErrorCode.InvalidRequest for invalid arguments (universal fallback)
// If your SDK requires ErrorCode.InvalidParams or another, change here.
