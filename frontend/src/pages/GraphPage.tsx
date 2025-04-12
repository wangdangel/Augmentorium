import React, { useRef, useEffect, useState } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

interface GraphData {
  nodes: any[];
  links: any[];
}

const NODE_TYPE_COLORS: Record<string, string> = {
  file: '#1f77b4',
  class: '#ff7f0e',
  function: '#2ca02c',
  variable: '#d62728',
  default: '#888'
};

const RELATION_TYPE_COLORS: Record<string, string> = {
  references: '#9467bd',
  imports: '#8c564b',
  default: '#bbb'
};

const GraphPage: React.FC = () => {
  const fgRef = useRef<any>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [filteredData, setFilteredData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    const fetchGraph = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch('/api/graph');
        if (!res.ok) throw new Error('Failed to fetch graph data');
        const data = await res.json();
        setGraphData(data);
        setFilteredData(data);
      } catch (e: any) {
        console.error(e);
        setError(e.message || 'Error fetching graph data');
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, []);

  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge').strength(-200);
    }
  }, [filteredData]);

  // File selection logic
  const fileNodes = graphData?.nodes?.filter((n: any) => n.type === "file" || n.group === "file") || [];

  const handleFileSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const fileId = e.target.value;
    setSelectedFile(fileId);
    setSelectedNode(null);
    if (!fileId || !graphData) {
      setFilteredData(graphData);
      return;
    }
    // Find all links where source or target is the file
    const links = graphData.links.filter((l: any) => l.source === fileId || l.target === fileId);
    // Find all node ids involved
    const nodeIds = new Set<string>();
    nodeIds.add(fileId);
    links.forEach((l: any) => {
      nodeIds.add(typeof l.source === "object" ? l.source.id : l.source);
      nodeIds.add(typeof l.target === "object" ? l.target.id : l.target);
    });
    // Filter nodes
    const nodes = graphData.nodes.filter((n: any) => nodeIds.has(n.id));
    setFilteredData({ nodes, links });
  };

  const handleShowAll = () => {
    setSelectedFile(null);
    setSelectedNode(null);
    setFilteredData(graphData);
  };

  // Node/edge highlighting logic
  const getHighlighted = () => {
    if (!selectedNode || !filteredData) return { nodes: new Set(), links: new Set() };
    const highlightNodes = new Set<string>();
    const highlightLinks = new Set<any>();
    highlightNodes.add(selectedNode.id);
    filteredData.links.forEach((l: any) => {
      if (l.source === selectedNode.id) {
        highlightNodes.add(typeof l.target === "object" ? l.target.id : l.target);
        highlightLinks.add(l);
      }
      if (l.target === selectedNode.id) {
        highlightNodes.add(typeof l.source === "object" ? l.source.id : l.source);
        highlightLinks.add(l);
      }
    });
    return { nodes: highlightNodes, links: highlightLinks };
  };

  const { nodes: highlightNodes, links: highlightLinks } = getHighlighted();

  // Search logic
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm || !graphData) return;
    const found = graphData.nodes.find(
      (n: any) =>
        (n.name && n.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        n.id.toLowerCase().includes(searchTerm.toLowerCase())
    );
    if (found) {
      setSelectedNode(found);
      // Optionally, center camera on node
      if (fgRef.current) {
        fgRef.current.centerAt(found.x || 0, found.y || 0, found.z || 0, 1000);
        fgRef.current.zoomToFit(300, 40, (node: any) => node.id === found.id);
      }
    }
  };

  // Camera controls
  const handleZoomToFit = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400);
    }
  };

  const handleResetCamera = () => {
    if (fgRef.current) {
      fgRef.current.cameraPosition({ x: 0, y: 0, z: 800 }, undefined, 1000);
    }
  };

  // Node/edge coloring
  const getNodeColor = (node: any) =>
    NODE_TYPE_COLORS[node.type] || NODE_TYPE_COLORS[node.group] || NODE_TYPE_COLORS.default;
  const getLinkColor = (link: any) =>
    RELATION_TYPE_COLORS[link.relation] || RELATION_TYPE_COLORS.default;

  return (
    <div style={{ height: '80vh', border: '1px solid lightgray', padding: 8 }}>
      <h1>Code Relationships</h1>
      {loading && <p>Loading graph...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
        <form onSubmit={handleSearch} style={{ display: 'inline' }}>
          <input
            type="text"
            placeholder="Search node by name or id"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{ marginRight: 4 }}
          />
          <button type="submit">Search</button>
        </form>
        <label>
          Focus on file:&nbsp;
          <select value={selectedFile || ""} onChange={handleFileSelect}>
            <option value="">(Show all files)</option>
            {fileNodes.map((n: any) => (
              <option key={n.id} value={n.id}>
                {n.name || n.id}
              </option>
            ))}
          </select>
        </label>
        <button onClick={handleShowAll} disabled={!selectedFile && !selectedNode}>
          Show All
        </button>
        <button onClick={handleZoomToFit}>Zoom to Fit</button>
        <button onClick={handleResetCamera}>Reset Camera</button>
      </div>
      <div style={{ marginBottom: 8 }}>
        <b>Legend:</b>
        <span style={{ marginLeft: 8 }}>
          {Object.entries(NODE_TYPE_COLORS).map(([type, color]) =>
            type !== "default" ? (
              <span key={type} style={{ color, marginRight: 12 }}>
                &#9632; {type}
              </span>
            ) : null
          )}
        </span>
        <span style={{ marginLeft: 16 }}>
          {Object.entries(RELATION_TYPE_COLORS).map(([rel, color]) =>
            rel !== "default" ? (
              <span key={rel} style={{ color, marginRight: 12 }}>
                &#8594; {rel}
              </span>
            ) : null
          )}
        </span>
      </div>
      <ForceGraph3D
        ref={fgRef}
        graphData={filteredData || { nodes: [], links: [] }}
        nodeAutoColorBy={undefined}
        nodeColor={node => highlightNodes && highlightNodes.has(node.id) ? '#FFD700' : getNodeColor(node)}
        linkColor={link => highlightLinks && highlightLinks.has(link) ? '#FFD700' : getLinkColor(link)}
        nodeLabel={(node: any) =>
          `<div>
            <b>${node.name || node.id}</b><br/>
            Type: ${node.type || node.group || 'unknown'}<br/>
            File: ${node.file_path || ''}<br/>
            ${node.start_line !== undefined ? `Lines: ${node.start_line}-${node.end_line}` : ''}
          </div>`
        }
        linkLabel={(link: any) =>
          `<div>
            <b>${link.relation || 'relation'}</b><br/>
            ${typeof link.source === "object" ? link.source.id : link.source} &rarr; ${typeof link.target === "object" ? link.target.id : link.target}
          </div>`
        }
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        onNodeClick={node => setSelectedNode(node)}
      />
    </div>
  );
};

export default GraphPage;
