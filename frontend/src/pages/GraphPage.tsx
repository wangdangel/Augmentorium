import React, { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

interface GraphData {
  nodes: any[];
  links: any[];
}

const GraphPage: React.FC = () => {
  const fgRef = useRef<any>();
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGraph = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch('/api/graph');
        if (!res.ok) throw new Error('Failed to fetch graph data');
        const data = await res.json();
        setGraphData(data);
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
  }, [graphData]);

  return (
    <div style={{ height: '80vh', border: '1px solid lightgray' }}>
      <h1>Code Relationships</h1>
      {loading && <p>Loading graph...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData || { nodes: [], links: [] }}
        nodeAutoColorBy="group"
        nodeLabel="id"
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
      />
    </div>
  );
};

export default GraphPage;
