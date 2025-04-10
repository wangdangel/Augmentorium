import React, { useState } from 'react';
import { uploadDocument } from '../api/documents';

interface DocumentUploadProps {
  onUploadSuccess: () => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    const success = await uploadDocument(selectedFile);
    if (success) {
      alert('Upload successful');
      setSelectedFile(null);
      onUploadSuccess();
    } else {
      alert('Upload failed');
    }
    setUploading(false);
  };

  return (
    <div style={{ marginBottom: '1rem' }}>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!selectedFile || uploading} style={{ marginLeft: '0.5rem' }}>
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
    </div>
  );
};

export default DocumentUpload;
