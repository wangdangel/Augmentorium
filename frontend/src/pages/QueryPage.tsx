import React, { useState, useEffect } from 'react';
import QueryOptions from '../components/QueryOptions';
import { fetchProjects, Project } from '../api/projects';

interface QueryResult {
  chunk_id: string;
  text: string;
  metadata: {
    file_path?: string;
    function_name?: string;
    class_name?: string;
    docstring?: string;
    [key: string]: any;
  };
  score: number;
}

const QueryPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoaded, setProjectsLoaded] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [query, setQuery] = useState('');
  const [context, setContext] = useState('');
  const [results, setResults] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nResults, setNResults] = useState(10);
  const [minScore, setMinScore] = useState(0);
  const [includeMetadata, setIncludeMetadata] = useState(true);

  useEffect(() => {
    let mounted = true;
    fetchProjects().then((data) => {
      if (mounted) {
        setProjects(data);
        setProjectsLoaded(true);
      }
    });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (projectsLoaded && projects.length > 0) setSelectedProject(projects[0].name);
  }, [projectsLoaded, projects]);

  const handleQuery = async () => {
    if (!query || !selectedProject) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/query/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project: selectedProject,
          query,
          n_results: nResults,
          min_score: minScore,
          include_metadata: includeMetadata,
        }),
      });
      const data = await res.json();
      setContext(data.context || '');
      setResults(data.results || []);
    } catch (e) {
      console.error(e);
      setError('Query failed');
    } finally {
      setLoading(false);
    }
  };

  const highlightMatches = (text: string) => {
    if (!query) return text;
    const re = new RegExp(query, 'gi');
    return text.split(re).reduce((acc, part, i, arr) =>
      i < arr.length - 1
        ? [...acc, part, <mark key={i}>{query}</mark>]
        : [...acc, part],
      [] as (string | React.ReactElement)[]
    );
  };

  return (
    <div>
      <h1>Query</h1>
      <div className="query-instructions">
        <strong>Tips for best results:</strong>
        <ul>
          <li>Use function or class names if you know them (e.g., <code>process_documents</code>).</li>
          <li>Paste a code snippet or line for precise matches.</li>
          <li>Try searching with docstring or comment text.</li>
          <li>Describe what the code does in plain English if unsure.</li>
          <li>Adjust "Results" and "Min Score" for more or fewer matches.</li>
        </ul>
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="project-select">Project: </label>
        <select
          id="project-select"
          value={selectedProject}
          onChange={e => setSelectedProject(e.target.value)}
        >
          {projects.map(p => (
            <option key={p.name} value={p.name}>{p.name}</option>
          ))}
        </select>
      </div>
      <input
        type="text"
        placeholder="Enter your query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="query-input"
        style={{ width: '60%', marginRight: '0.5rem' }}
      />
      <button onClick={handleQuery} disabled={loading || !selectedProject || !query}>
        {loading ? 'Querying...' : 'Query'}
      </button>
      <button onClick={() => handleExport(context)} style={{ marginLeft: '0.5rem' }}>
        Export Context
      </button>
      <QueryOptions
        nResults={nResults}
        setNResults={setNResults}
        minScore={minScore}
        setMinScore={setMinScore}
        includeMetadata={includeMetadata}
        setIncludeMetadata={setIncludeMetadata}
      />
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <h2>Context Preview</h2>
      <pre className="context-preview">{context}</pre>
      <h2>Results</h2>
      <ul>
        {results.map((r) => (
          <li key={r.chunk_id} style={{ marginBottom: '1rem' }}>
            <div><strong>Score:</strong> {r.score.toFixed(2)}</div>
            {r.metadata.file_path && <div><strong>File:</strong> {r.metadata.file_path}</div>}
            {r.metadata.class_name && <div><strong>Class:</strong> {r.metadata.class_name}</div>}
            {r.metadata.function_name && <div><strong>Function:</strong> {r.metadata.function_name}</div>}
            {r.metadata.docstring && <div><strong>Docstring:</strong> {r.metadata.docstring}</div>}
            <pre className="result-text-box">
              {highlightMatches(r.text)}
            </pre>
          </li>
        ))}
      </ul>
    </div>
  );
};

const handleExport = (context: string) => {
  const blob = new Blob([context], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'context.txt';
  a.click();
  URL.revokeObjectURL(url);
};

export default QueryPage;
