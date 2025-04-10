import React, { useState } from 'react';
import { DocumentInfo, reindexDocument } from '../api/documents';

interface DocumentListProps {
  documents: DocumentInfo[];
  onRefresh: () => void;
}

const DocumentList: React.FC<DocumentListProps> = ({ documents, onRefresh }) => {
  const [reindexingId, setReindexingId] = useState<string | null>(null);

  const handleReindex = async (docId: string) => {
    setReindexingId(docId);
    const success = await reindexDocument(docId);
    if (!success) {
      alert('Failed to reindex document');
    } else {
      await onRefresh();
    }
    setReindexingId(null);
  };

  return (
    <div>
      <h2>Indexed Documents</h2>
      {documents.length === 0 ? (
        <p>No documents found.</p>
      ) : (
        <ul>
          {documents.map((doc) => (
            <li key={doc.id} style={{ marginBottom: '1rem' }}>
              <div><strong>{doc.name}</strong> ({(doc.size / 1024).toFixed(1)} KB) - {doc.status}</div>
              {doc.chunkCount !== undefined && <div>Chunks: {doc.chunkCount}</div>}
              {doc.lastIndexed && <div>Last Indexed: {new Date(doc.lastIndexed).toLocaleString()}</div>}
              <button
                onClick={() => handleReindex(doc.id)}
                disabled={reindexingId === doc.id}
                style={{ marginTop: '0.5rem' }}
              >
                {reindexingId === doc.id ? 'Re-indexing...' : 'Re-index'}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default DocumentList;
