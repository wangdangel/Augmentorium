import React from 'react';

const MCPPage: React.FC = () => {
  return (
    <div>
      <h1>MCP Tools</h1>
      <p>Interact with MCP server tools and resources here.</p>
      <section style={{marginTop: '2em'}}>
        <h2>Augmentorium API Endpoints Reference</h2>
        <p style={{color: 'gray'}}>Below is a comprehensive list of backend API endpoints, grouped by feature. Click to expand for details and usage examples.</p>

        {/* Graph Endpoints */}
        <h3 style={{marginTop: '2em'}}>Graph Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th><th>Example</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/graph/</code></td>
              <td>Get the full code relationship graph for a project.</td>
              <td><code>?project=NAME</code></td>
              <td><pre>{`curl -X GET "http://localhost:6655/api/graph/?project=demo"`}</pre></td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/graph/neighbors/</code></td>
              <td>Get neighbors (callers, callees, imports, etc) for a node in a project.</td>
              <td><pre>{`{ "project": "NAME", "node_id": "NODE_ID" }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/graph/neighbors/ -H "Content-Type: application/json" -d '{"project": "demo", "node_id": "my_func"}'`}</pre></td>
            </tr>
          </tbody>
        </table>

        {/* Project & File Endpoints */}
        <h3 style={{marginTop: '2em'}}>Project & File Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th><th>Example</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/projects/</code></td>
              <td>List all projects with metadata.</td>
              <td>None</td>
              <td><pre>{`curl -X GET http://localhost:6655/api/projects/`}</pre></td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/projects/</code></td>
              <td>Add a new project.</td>
              <td><pre>{`{ "path": "/path/to/project", "name": "demo" }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/projects/ -H "Content-Type: application/json" -d '{"path": "/path/to/project", "name": "demo"}'`}</pre></td>
            </tr>
            <tr>
              <td>DELETE</td>
              <td><code>/api/projects/&lt;name&gt;</code></td>
              <td>Delete a project.</td>
              <td><code>name</code> in path</td>
              <td><pre>{`curl -X DELETE http://localhost:6655/api/projects/demo`}</pre></td>
            </tr>
            <tr>
              <td>GET</td>
              <td><code>/api/files/</code></td>
              <td>List indexed files in a project.</td>
              <td><code>?project=NAME&max_files=20</code></td>
              <td><pre>{`curl -X GET "http://localhost:6655/api/files/?project=demo"`}</pre></td>
            </tr>
          </tbody>
        </table>

        {/* Indexer & Stats Endpoints */}
        <h3 style={{marginTop: '2em'}}>Indexer & Stats Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th><th>Example</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/indexer/status</code></td>
              <td>Get current indexer status.</td>
              <td>None</td>
              <td><pre>{`curl -X GET http://localhost:6655/api/indexer/status`}</pre></td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/indexer/status</code></td>
              <td>Update indexer status (internal use).</td>
              <td><pre>{`{ "projects": [...] }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/indexer/status -H "Content-Type: application/json" -d '{"projects": [{"name": "demo", ...}]}'`}</pre></td>
            </tr>
            <tr>
              <td>GET</td>
              <td><code>/api/stats/</code></td>
              <td>Get stats for a project.</td>
              <td><code>?project=NAME</code></td>
              <td><pre>{`curl -X GET "http://localhost:6655/api/stats/?project=demo"`}</pre></td>
            </tr>
          </tbody>
        </table>

        {/* Document Endpoints */}
        <h3 style={{marginTop: '2em'}}>Document Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th><th>Example</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/documents/</code></td>
              <td>List indexed documents for a project.</td>
              <td><code>?project=NAME</code></td>
              <td><pre>{`curl -X GET "http://localhost:6655/api/documents/?project=demo"`}</pre></td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/documents/upload</code></td>
              <td>Upload a new document to a project.</td>
              <td><pre>{`{ "project": "NAME", "name": "file.txt", "content": "..." }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/documents/upload -H "Content-Type: application/json" -d '{"project": "demo", "name": "file.txt", "content": "..."}'`}</pre></td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/documents/&lt;doc_id&gt;/reindex</code></td>
              <td>Reindex a document for a project.</td>
              <td><pre>{`{ "project": "NAME" }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/documents/doc1/reindex -H "Content-Type: application/json" -d '{"project": "demo"}'`}</pre></td>
            </tr>
          </tbody>
        </table>

        {/* Query & Search Endpoints */}
        <h3 style={{marginTop: '2em'}}>Query & Search Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th><th>Example</th></tr></thead>
          <tbody>
            <tr>
              <td>POST</td>
              <td><code>/api/query/</code></td>
              <td>Run a search/query over the codebase for a project.</td>
              <td><pre>{`{ "project": "NAME", "query": "..." }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/query/ -H "Content-Type: application/json" -d '{"project": "demo", "query": "import requests"}'`}</pre></td>
            </tr>
            <tr>
              <td>DELETE</td>
              <td><code>/api/query/cache</code></td>
              <td>Clear query cache for a project.</td>
              <td><code>?project=NAME</code></td>
              <td><pre>{`curl -X DELETE "http://localhost:6655/api/query/cache?project=demo"`}</pre></td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/chunks/search</code></td>
              <td>Semantic search for code chunks/passages in a project.</td>
              <td><pre>{`{ "project": "NAME", "query": "...", "n_results": 5 }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/chunks/search -H "Content-Type: application/json" -d '{"project": "demo", "query": "def ", "n_results": 3}'`}</pre></td>
            </tr>
          </tbody>
        </table>

        {/* Explainability Endpoints */}
        <h3 style={{marginTop: '2em'}}>Explainability</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th><th>Example</th></tr></thead>
          <tbody>
            <tr>
              <td>POST</td>
              <td><code>/api/explain/</code></td>
              <td>Explain why a result was retrieved (vector score, graph path, etc).</td>
              <td><pre>{`{ "project": "NAME", "query": "...", "result": {...} }`}</pre></td>
              <td><pre>{`curl -X POST http://localhost:6655/api/explain/ -H "Content-Type: application/json" -d '{"project": "demo", "query": "...", "result": {...}}'`}</pre></td>
            </tr>
          </tbody>
        </table>

        {/* Cache Endpoints */}
        <h3 style={{marginTop: '2em'}}>Cache Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th><th>Example</th></tr></thead>
          <tbody>
            <tr>
              <td>DELETE</td>
              <td><code>/api/cache/</code></td>
              <td>Clear general cache for a project.</td>
              <td><code>?project=NAME</code></td>
              <td><pre>{`curl -X DELETE "http://localhost:6655/api/cache/?project=demo"`}</pre></td>
            </tr>
          </tbody>
        </table>

        <style>{`
          .api-table { width: 100%; border-collapse: collapse; margin-bottom: 2em; }
          .api-table th, .api-table td { border: 1px solid #333; padding: 8px; background: #181818; color: #f1f1f1; }
          .api-table th { background: #232323; color: #fff; }
          .api-table td { vertical-align: top; }
          .api-table code, .api-table pre { background: #222; color: #fff; padding: 2px 5px; border-radius: 3px; font-size: 1em; word-break: break-all; white-space: pre-wrap; }
          .api-table td code, .api-table td pre { display: block; overflow-x: auto; max-width: 100%; }
          .api-table pre { margin: 0; font-size: 0.96em; background: #222; color: #fff; padding: 6px 10px; border-radius: 3px; }
          .api-table th:nth-child(2), .api-table td:nth-child(2) { min-width: 200px; max-width: 340px; }
          .api-table th:nth-child(4), .api-table td:nth-child(4) { min-width: 180px; max-width: 400px; }
        `}</style>
      </section>
    </div>
  );
};

export default MCPPage;
