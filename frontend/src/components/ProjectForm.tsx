import React, { useState } from 'react';

interface ProjectFormProps {
  onAdd: (path: string, name?: string) => Promise<boolean>;
}

const ProjectForm: React.FC<ProjectFormProps> = ({ onAdd }) => {
  const [path, setPath] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!path) return;
    setLoading(true);
    const cleanedPath = path.trim().replace(/^["']|["']$/g, '');
    const success = await onAdd(cleanedPath, name);
    if (success) {
      setPath('');
      setName('');
    } else {
      alert('Failed to add project');
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '1rem' }}>
      <input
        type="text"
        placeholder="Project path"
        value={path}
        onChange={(e) => setPath(e.target.value)}
        style={{ marginRight: '0.5rem' }}
        required
      />
      <input
        type="text"
        placeholder="Project name (optional)"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{ marginRight: '0.5rem' }}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Adding...' : 'Add Project'}
      </button>
    </form>
  );
};

export default ProjectForm;
