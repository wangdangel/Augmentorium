import React, { useRef, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

/**
 * TODO:
 * - Replace mock data with backend API data.
 * - Add filters, expand/collapse, tooltips.
 * - Style nodes/edges based on type/status.
 */

const mockData = {
  nodes: [
    { id: 'file1.py', group: 'file' },
    { id: 'file2.py', group: 'file' },
    { id: 'ClassA', group: 'class' },
    { id: 'func_a', group: 'function' },
    { id: 'func_b', group: 'function' },
  ],
  links: [
    { source: 'file1.py', target: 'ClassA' },
    { source: 'ClassA', target: 'func_a' },
    { source: 'file2.py', target: 'func_b' },
    { source: 'func_a', target: 'func_b' },
  ],
};

const GraphPage: React.FC = () => {
  const fgRef = useRef<any>();

  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge').strength(-200);
    }
  }, []);

  return (
    <div style={{ height: '80vh' }}>
      <h1>Code Relationships</h1>
      <ForceGraph2D
        ref={fgRef}
        graphData={mockData}
        nodeAutoColorBy="group"
        nodeLabel="id"
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
      />
    </div>
  );
};

export default GraphPage;
