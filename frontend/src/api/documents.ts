export interface DocumentInfo {
  id: string;
  name: string;
  size: number;
  uploaded_at: string;
  status: string;
  chunkCount?: number;
  lastIndexed?: string;
}

export async function fetchDocuments(): Promise<DocumentInfo[]> {
  try {
    const res = await fetch('/api/documents');
    if (!res.ok) {
      console.error('Failed to fetch documents');
      return [];
    }
    const data = await res.json();
    return data.documents || [];
  } catch (e) {
    console.error('Error fetching documents:', e);
    return [];
  }
}

export async function uploadDocument(file: File): Promise<boolean> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/documents/upload', {
      method: 'POST',
      body: formData,
    });
    return res.ok;
  } catch (e) {
    console.error('Error uploading document:', e);
    return false;
  }
}

export async function reindexProject(): Promise<boolean> {
  try {
    const res = await fetch('/api/documents/reindex', {
      method: 'POST',
    });
    return res.ok;
  } catch (e) {
    console.error('Error triggering reindex:', e);
    return false;
  }
}

export async function reindexDocument(docId: string): Promise<boolean> {
  try {
    const res = await fetch(`/api/documents/${encodeURIComponent(docId)}/reindex`, {
      method: 'POST',
    });
    return res.ok;
  } catch (e) {
    console.error('Error reindexing document:', e);
    return false;
  }
}

/**
 * Placeholder: Fetch indexing progress/status.
 * Backend should expose an endpoint returning progress info.
 */
export async function fetchIndexingStatus(): Promise<any> {
  try {
    const res = await fetch('/api/indexing/status');
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
