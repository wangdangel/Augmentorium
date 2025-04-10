import React from 'react';

interface QueryOptionsProps {
  nResults: number;
  setNResults: (val: number) => void;
  minScore: number;
  setMinScore: (val: number) => void;
  includeMetadata: boolean;
  setIncludeMetadata: (val: boolean) => void;
}

const QueryOptions: React.FC<QueryOptionsProps> = ({
  nResults,
  setNResults,
  minScore,
  setMinScore,
  includeMetadata,
  setIncludeMetadata,
}) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ marginRight: '1rem' }}>
        Results:
        <input
          type="number"
          min={1}
          max={100}
          value={nResults}
          onChange={(e) => setNResults(Number(e.target.value))}
          style={{ width: '4rem', marginLeft: '0.5rem' }}
        />
      </label>
      <label style={{ marginRight: '1rem' }}>
        Min Score:
        <input
          type="number"
          step={0.01}
          min={0}
          max={1}
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
          style={{ width: '4rem', marginLeft: '0.5rem' }}
        />
      </label>
      <label style={{ marginRight: '1rem' }}>
        Include Metadata:
        <input
          type="checkbox"
          checked={includeMetadata}
          onChange={(e) => setIncludeMetadata(e.target.checked)}
          style={{ marginLeft: '0.5rem' }}
        />
      </label>
    </div>
  );
};

export default QueryOptions;
