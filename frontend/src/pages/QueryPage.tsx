import React, { useState } from 'react';
import QueryOptions from '../components/QueryOptions';

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
  const [query, setQuery] = useState('');
  const [context, setContext] = useState('');
  const [results, setResults] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [nResults, setNResults] = useState(10);
  const [minScore, setMinScore] = useState(0);
  const [includeMetadata, setIncludeMetadata] = useState(true);

  const handleQuery = async () => {
    if (!query) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/query/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
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

  const handleExport = () => {
    const blob = new Blob([context], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'context.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const highlightMatches = (text: string) => {
    if (!query.trim()) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, idx) =>
      part.toLowerCase() === query.toLowerCase() ? <mark key={idx}>{part}</mark> : part
    );
  };

  return (
    <div>
      <h1>Query</h1>
      <div style={{ background: '#f8f9fa', border: '1px solid #ddd', borderRadius: '6px', padding: '0.75rem', marginBottom: '1rem', fontSize: '0.98rem' }}>
        <strong>Tips for best results:</strong>
        <ul style={{ margin: '0.5em 0 0 1.2em', padding: 0 }}>
          <li>Use function or class names if you know them (e.g., <code>process_documents</code>).</li>
          <li>Paste a code snippet or line for precise matches.</li>
          <li>Try searching with docstring or comment text.</li>
          <li>Describe what the code does in plain English if unsure.</li>
          <li>Adjust "Results" and "Min Score" for more or fewer matches.</li>
        </ul>
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          placeholder="Enter your query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ width: '60%', marginRight: '0.5rem' }}
        />
        <button onClick={handleQuery} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
        <button onClick={handleExport} style={{ marginLeft: '0.5rem' }}>
          Export Context
        </button>
      </div>
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
      <pre>{context}</pre>
      <h2>Results</h2>
      <ul>
        {results.map((r) => (
          <li key={r.chunk_id} style={{ marginBottom: '1rem' }}>
            <div><strong>Score:</strong> {r.score.toFixed(2)}</div>
            {r.metadata.file_path && <div><strong>File:</strong> {r.metadata.file_path}</div>}
            {r.metadata.class_name && <div><strong>Class:</strong> {r.metadata.class_name}</div>}
            {r.metadata.function_name && <div><strong>Function:</strong> {r.metadata.function_name}</div>}
            {r.metadata.docstring && <div><strong>Docstring:</strong> {r.metadata.docstring}</div>}
            <pre style={{ background: '#f4f4f4', padding: '0.5rem' }}>
              {highlightMatches(r.text)}
            </pre>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default QueryPage;
