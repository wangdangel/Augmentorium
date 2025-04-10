import React, { useState } from 'react';
import { Project } from '../api/projects';

interface ProjectListProps {
  projects: Project[];
  activeProjectName?: string;
  onRemove: (name: string) => Promise<boolean>;
  onSetActive: (path: string) => Promise<boolean>;
}

const ProjectList: React.FC<ProjectListProps> = ({ projects, activeProjectName, onRemove, onSetActive }) => {
  const [deleting, setDeleting] = useState<string | null>(null);
  const [settingActive, setSettingActive] = useState<string | null>(null);

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
    <ul>
      {projects.map((proj) => (
        <li key={proj.name} style={{ marginBottom: '1rem' }}>
          <div>
            <strong>{proj.name}</strong> {activeProjectName === proj.name && <span style={{ color: 'green' }}>(Active)</span>}
          </div>
          <div>Path: {proj.path}</div>
          {proj.status && <div>Status: {proj.status}</div>}
          {proj.size !== undefined && <div>Size: {(proj.size / (1024 * 1024)).toFixed(2)} MB</div>}
          {proj.lastIndexed && <div>Last Indexed: {new Date(proj.lastIndexed).toLocaleString()}</div>}
          <button
            style={{ marginRight: '0.5rem', marginTop: '0.5rem' }}
            onClick={() => handleSetActive(proj.path)}
            disabled={settingActive === proj.path}
          >
            {settingActive === proj.path ? 'Setting...' : 'Set Active'}
          </button>
          <button
            onClick={() => handleDelete(proj.name)}
            disabled={deleting === proj.name}
          >
            {deleting === proj.name ? 'Removing...' : 'Remove'}
          </button>
        </li>
      ))}
    </ul>
  );
};

export default ProjectList;
