import React, { useRef, useEffect, useState } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { fetchProjects, Project } from '../api/projects';

interface GraphData {
  nodes: any[];
  links: any[];
}

const NODE_TYPE_COLORS: Record<string, string> = {
  file: '#1f77b4',
  class: '#ff7f0e',
  function: '#2ca02c',
  variable: '#d62728',
  module: '#888',
  default: '#888'
};

const RELATION_TYPE_COLORS: Record<string, string> = {
  references: '#9467bd',
  imports: '#8c564b',
  default: '#bbb'
};

const GraphPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoaded, setProjectsLoaded] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [filteredData, setFilteredData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const fgRef = useRef<any>(null);

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

  useEffect(() => {
    if (!selectedProject) return;
    setLoading(true);
    setError(null);
    fetch(`/api/graph?project=${encodeURIComponent(selectedProject)}`)
      .then(res => res.json())
      .then(data => {
        setGraphData(data);
        setFilteredData(data);
      })
      .catch(() => {
        setError('Failed to load graph');
      })
      .finally(() => setLoading(false));
  }, [selectedProject]);

  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge').strength(-200);
    }
  }, [filteredData]);

  // Helper to extract unique file nodes (now using 'module' as file type)
  const fileNodes = graphData?.nodes.filter(n => n.type === 'module') || [];
  const fileNames = Array.from(new Set(fileNodes.map(n => n.name))).filter(Boolean);

  // Handle file selection and filter graph
  useEffect(() => {
    if (!graphData || !selectedFile) {
      setFilteredData(graphData);
      return;
    }
    // Find the selected file node by name
    const fileNode = graphData.nodes.find(n => n.type === 'module' && n.name === selectedFile);
    if (!fileNode) {
      setFilteredData({ nodes: [], links: [] });
      return;
    }
    // Find links where the file node is source or target
    const connectedLinks = graphData.links.filter(l => l.source === fileNode.id || l.target === fileNode.id);
    // Find connected node ids
    const connectedNodeIds = new Set([
      fileNode.id,
      ...connectedLinks.map(l => l.source),
      ...connectedLinks.map(l => l.target)
    ]);
    // Filter nodes and links
    const filteredNodes = graphData.nodes.filter(n => connectedNodeIds.has(n.id));
    setFilteredData({ nodes: filteredNodes, links: connectedLinks });
  }, [graphData, selectedFile]);

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
      if (fgRef.current) {
        // Use cameraPosition for 3D centering
        if (typeof fgRef.current.cameraPosition === 'function') {
          fgRef.current.cameraPosition(
            { x: found.x || 0, y: found.y || 0, z: found.z || 0 },
            undefined,
            1000
          );
        } else {
          console.warn('cameraPosition is not a function on fgRef.current:', fgRef.current);
        }
        if (typeof fgRef.current.zoomToFit === 'function') {
          fgRef.current.zoomToFit(300, 40, (node: any) => node.id === found.id);
        } else {
          console.warn('zoomToFit is not a function on fgRef.current:', fgRef.current);
        }
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
    <div>
      <h1>Code Relationships</h1>
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
      {loading && <p>Loading graph...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {graphData && !loading && (
        <div style={{ height: '80vh', border: '1px solid lightgray', padding: 8 }}>
          <label htmlFor="file-select">Select file: </label>
          <select
            id="file-select"
            value={selectedFile || ''}
            onChange={e => setSelectedFile(e.target.value || null)}
          >
            <option value="">All files</option>
            {fileNames.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
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
      )}
    </div>
  );
};

export default GraphPage;
