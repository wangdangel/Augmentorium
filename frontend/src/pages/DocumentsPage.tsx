import React, { useEffect, useState } from 'react';
import { fetchDocuments, DocumentInfo } from '../api/documents';
import DocumentUpload from '../components/DocumentUpload';
import ReindexButton from '../components/ReindexButton';
import DocumentList from '../components/DocumentList';

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (e) {
      console.error(e);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div>
      <h1>Documents & Indexing</h1>
      <DocumentUpload onUploadSuccess={loadDocuments} />
      <ReindexButton />
      {loading && <p>Loading documents...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <DocumentList documents={documents} onRefresh={loadDocuments} />
    </div>
  );
};

export default DocumentsPage;
