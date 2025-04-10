import React, { useState } from 'react';

const ClearCacheButton: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleClearCache = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/cache', { method: 'DELETE' });
      if (res.ok) {
        alert('Cache cleared');
      } else {
        alert('Failed to clear cache');
      }
    } catch (e) {
      console.error(e);
      alert('Error clearing cache');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleClearCache} disabled={loading}>
      {loading ? 'Clearing...' : 'Clear Query Cache'}
    </button>
  );
};

export default ClearCacheButton;
