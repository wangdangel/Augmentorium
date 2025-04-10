import React, { useRef, useEffect } from 'react';
// Corrected import: Import from the 'react-force-graph-2d' package
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
  // Consider using a more specific type for the ref if available from the library's types
  const fgRef = useRef<any>();

  useEffect(() => {
    if (fgRef.current) {
      // Access d3Force method
      fgRef.current.d3Force('charge').strength(-200);
      // Example: Zoom to fit nodes after initial render
      // fgRef.current.zoomToFit(400, 50); // Adjust duration and padding as needed
    }
  }, []);

  return (
    <div style={{ height: '80vh', border: '1px solid lightgray' }}> {/* Added border for visibility */}
      <h1>Code Relationships</h1>
      <ForceGraph2D
        ref={fgRef}
        graphData={mockData}
        nodeAutoColorBy="group"
        nodeLabel="id"
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
      // Optional: Set width/height explicitly if needed, though container style often suffices
      // width={/* calculate width */}
      // height={/* calculate height */}
      />
    </div>
  );
};

export default GraphPage;