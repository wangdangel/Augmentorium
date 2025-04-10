import React, { useState } from 'react';
import { reindexProject } from '../api/documents';

const ReindexButton: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleReindex = async () => {
    setLoading(true);
    const success = await reindexProject();
    if (success) {
      alert('Reindex triggered successfully');
    } else {
      alert('Failed to trigger reindex');
    }
    setLoading(false);
  };

  return (
    <div style={{ marginBottom: '1rem' }}>
      <button onClick={handleReindex} disabled={loading}>
        {loading ? 'Re-indexing...' : 'Re-index Project'}
      </button>
    </div>
  );
};

export default ReindexButton;
