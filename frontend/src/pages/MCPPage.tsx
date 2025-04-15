import React from 'react';

const MCPPage: React.FC = () => {
  return (
    <div>
      <h1>MCP Tools</h1>
      <p>Interact with MCP server tools and resources here.</p>
      <section style={{marginTop: '2em'}}>
        <h2>Augmentorium API Endpoints Reference</h2>
        <p style={{color: 'gray'}}>Below is a comprehensive list of backend API endpoints, grouped by feature. Click to expand for details and usage examples.</p>
        <h3 style={{marginTop: '2em'}}>Graph Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/graph/</code></td>
              <td>Get the full code relationship graph for the active project.</td>
              <td>None (uses active project)</td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/graph/neighbors/</code></td>
              <td>Get neighbors (callers, callees, imports, etc) for a node in a project.</td>
              <td><pre>{`{ "project": "name", "node_id": "id" }`}</pre></td>
            </tr>
          </tbody>
        </table>
        <h3 style={{marginTop: '2em'}}>Project & File Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/projects/</code></td>
              <td>List all projects with metadata.</td>
              <td>None</td>
            </tr>
            <tr>
              <td>GET</td>
              <td><code>/api/files/</code></td>
              <td>List indexed files in a project.</td>
              <td><code>?project=NAME&max_files=20</code></td>
            </tr>
          </tbody>
        </table>
        <h3 style={{marginTop: '2em'}}>Indexer & Stats Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/indexer/status</code></td>
              <td>Get current indexer status.</td>
              <td>None</td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/indexer/status</code></td>
              <td>Update indexer status (internal use).</td>
              <td><pre>{`{ "projects": [...] }`}</pre></td>
            </tr>
            <tr>
              <td>GET</td>
              <td><code>/api/stats/</code></td>
              <td>Get stats for a project.</td>
              <td><code>?project=NAME</code></td>
            </tr>
          </tbody>
        </table>
        <h3 style={{marginTop: '2em'}}>Document Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th></tr></thead>
          <tbody>
            <tr>
              <td>GET</td>
              <td><code>/api/documents/</code></td>
              <td>List indexed documents.</td>
              <td>None</td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/documents/upload</code></td>
              <td>Upload a new document.</td>
              <td>multipart/form-data</td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/documents/&lt;doc_id&gt;/reindex</code></td>
              <td>Reindex a document.</td>
              <td>None</td>
            </tr>
          </tbody>
        </table>
        <h3 style={{marginTop: '2em'}}>Query & Search Endpoints</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th></tr></thead>
          <tbody>
            <tr>
              <td>POST</td>
              <td><code>/api/query/</code></td>
              <td>Run a search/query over the codebase.</td>
              <td><pre>{`{ "query": "...", ... }`}</pre></td>
            </tr>
            <tr>
              <td>DELETE</td>
              <td><code>/api/query/cache</code></td>
              <td>Clear query cache.</td>
              <td>None</td>
            </tr>
            <tr>
              <td>POST</td>
              <td><code>/api/chunks/search</code></td>
              <td>Semantic search for code chunks/passages.</td>
              <td><pre>{`{ "project": "...", "query": "...", "n_results": 5 }`}</pre></td>
            </tr>
          </tbody>
        </table>
        <h3 style={{marginTop: '2em'}}>Explainability</h3>
        <table className="api-table">
          <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Params/Body</th></tr></thead>
          <tbody>
            <tr>
              <td>POST</td>
              <td><code>/api/explain/</code></td>
              <td>Explain why a result was retrieved (vector score, graph path, etc).</td>
              <td><pre>{`{ "project": "...", "query": "...", "result": {...} }`}</pre></td>
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
