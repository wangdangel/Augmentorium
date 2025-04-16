import React, { useState } from 'react';
import { Project, reinitializeProject } from '../api/projects';

interface ProjectListProps {
  projects: Project[];
  onRemove: (name: string) => Promise<boolean>;
}

const ProjectList: React.FC<ProjectListProps> = ({ projects, onRemove }) => {
  const [deleting, setDeleting] = useState<string | null>(null);
  const [reinitializing, setReinitializing] = useState<string | null>(null);

  const handleDelete = async (name: string) => {
    const confirmed = window.confirm(`Are you sure you want to remove project "${name}"?`);
    if (!confirmed) return;
    setDeleting(name);
    const success = await onRemove(name);
    if (!success) {
      alert('Failed to remove project');
    }
    setDeleting(null);
  };

  const handleReinitialize = async (name: string) => {
    const confirmed = window.confirm(`Are you sure you want to reinitialize project "${name}"? This will delete and rebuild all metadata.`);
    if (!confirmed) return;
    setReinitializing(name);
    const success = await reinitializeProject(name);
    if (!success) {
      alert('Failed to reinitialize project');
    }
    setReinitializing(null);
  };

  return (
    <div>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {projects.map((proj) => (
          <li key={proj.name} style={{
            marginBottom: '1rem',
            border: '1px solid var(--project-card-border, #e0e0e0)',
            borderRadius: '8px',
            padding: '1rem',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
            background: 'var(--project-card-bg, #fafbfc)',
            maxWidth: 480
          }}>
            <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--project-card-title, #222)' }}>{proj.name}</div>
            <div style={{ color: 'var(--project-card-path, #888)', fontSize: '0.97rem', marginBottom: '0.4rem' }}>{proj.path}</div>
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '0.4rem', fontSize: '0.96rem' }}>
              {typeof proj.size === 'number' && (
                <span style={{ color: 'var(--project-card-size, #bbb)' }}>
                  <strong>Size:</strong> {(proj.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              )}
              {proj.status && (
                <span style={{ color: proj.status === 'indexing' ? '#e67e22' : 'var(--project-card-status, #27ae60)' }}>
                  <strong>Status:</strong> {proj.status}
                </span>
              )}
            </div>
            {proj.lastIndexed && (
              <div style={{ color: 'var(--project-card-last, #888)', fontSize: '0.95rem', marginBottom: '0.5rem' }}>
                <strong>Last Indexed:</strong> {new Date(proj.lastIndexed).toLocaleString()}
              </div>
            )}
            <div>
              <button
                style={{ marginRight: '0.7rem' }}
                onClick={() => handleDelete(proj.name)}
                disabled={deleting === proj.name}
              >
                {deleting === proj.name ? 'Removing...' : 'Remove'}
              </button>
              <button
                onClick={() => handleReinitialize(proj.name)}
                disabled={reinitializing === proj.name}
              >
                {reinitializing === proj.name ? 'Reinitializing...' : 'Reinitialize'}
              </button>
            </div>
          </li>
        ))}
      </ul>
      <p style={{ fontStyle: 'italic', marginTop: '1rem' }}>
        All open projects are continuously indexed in the background.
      </p>
    </div>
  );
};

export default ProjectList;
