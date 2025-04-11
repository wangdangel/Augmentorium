import React, { useState } from 'react';
import { Project, reindexSpecificProject } from '../api/projects';

interface ProjectListProps {
  projects: Project[];
  activeProjectName?: string;
  onRemove: (name: string) => Promise<boolean>;
  onSetActive: (path: string) => Promise<boolean>;
}

const ProjectList: React.FC<ProjectListProps> = ({ projects, activeProjectName, onRemove, onSetActive }) => {
  const [deleting, setDeleting] = useState<string | null>(null);
  const [settingActive, setSettingActive] = useState<string | null>(null);

  const activeStyle: React.CSSProperties = {
    border: '3px solid #4CAF50',
    backgroundColor: '#e8f5e9',
    color: '#000',
    borderRadius: '8px',
    padding: '0.5rem',
    boxShadow: '0 0 10px rgba(76, 175, 80, 0.3)',
  };

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

  const handleSetActive = async (path: string) => {
    setSettingActive(path);
    const success = await onSetActive(path);
    if (!success) {
      alert('Failed to set active project');
    }
    setSettingActive(null);
  };

  return (
    <div>
      <ul>
        {projects.map((proj) => {
          const isActive = activeProjectName === proj.name;
          return (
            <li
              key={proj.name}
              style={{
                marginBottom: '1rem',
                ...(isActive ? activeStyle : {}),
              }}
            >
              <div>
                <strong>{proj.name}</strong>{' '}
                {isActive && (
                  <span style={{ color: 'green', fontWeight: 'bold' }}>
                    (Active Project)
                  </span>
                )}
              </div>
            <div>Path: {proj.path}</div>
            {proj.status && <div>Status: {proj.status}</div>}
            {proj.size !== undefined && <div>Size: {(proj.size / (1024 * 1024)).toFixed(2)} MB</div>}
            {proj.lastIndexed && <div>Last Indexed: {new Date(proj.lastIndexed).toLocaleString()}</div>}
            <button
              style={{ marginRight: '0.5rem', marginTop: '0.5rem' }}
              onClick={() => handleSetActive(proj.name)}
              disabled={settingActive === proj.name}
            >
              {settingActive === proj.name ? 'Setting...' : 'Set Active'}
            </button>
            <button
              style={{ marginRight: '0.5rem', marginTop: '0.5rem' }}
              onClick={async () => {
                const confirmed = window.confirm(`Reindex project "${proj.name}"? This may take a while.`);
                if (!confirmed) return;
                const success = await reindexSpecificProject(proj.name);
                if (success) {
                  alert('Reindex triggered successfully');
                } else {
                  alert('Failed to trigger reindex');
                }
              }}
            >
              Reindex
            </button>
            <button
              onClick={() => handleDelete(proj.name)}
              disabled={deleting === proj.name}
            >
              {deleting === proj.name ? 'Removing...' : 'Remove'}
            </button>
          </li>
          );
        })}
      </ul>
      <p style={{ fontStyle: 'italic', marginTop: '1rem' }}>
        All open projects are continuously indexed in the background.
        The <span style={{ fontWeight: 'bold' }}>active project</span> is used for document uploads, queries, and graph visualization.
        You can switch the active project at any time.
      </p>
    </div>
  );
};

export default ProjectList;
