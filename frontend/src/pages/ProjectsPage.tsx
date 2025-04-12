import React, { useEffect, useState } from 'react';
import { fetchProjects, addProject, removeProject, getActiveProject, setActiveProject, Project } from '../api/projects';
import ProjectForm from '../components/ProjectForm';
import ProjectList from '../components/ProjectList';

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectName, setActiveProjectName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects();
      const active = await getActiveProject();
      setActiveProjectName(active?.name || null);

      let mergedProjects = data;
      if (active) {
        const exists = data.some((p) => p.name === active.name || p.path === active.path);
        if (!exists) {
          mergedProjects = [...data, active];
        }
      }
      setProjects(mergedProjects);
    } catch (e) {
      console.error(e);
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  // Poll only status, size, lastIndexed fields every 5s, without setting loading
  const refreshProjectStatuses = async () => {
    try {
      const data = await fetchProjects();
      setProjects((prevProjects) => {
        // Map by name for quick lookup
        const dataMap = new Map(data.map(p => [p.name, p]));
        return prevProjects.map((proj) => {
          const updated = dataMap.get(proj.name);
          if (updated) {
            return {
              ...proj,
              status: updated.status,
              size: updated.size,
              lastIndexed: updated.lastIndexed,
            };
          }
          return proj;
        });
      });
    } catch (e) {
      // Silent fail for background refresh
    }
  };

  useEffect(() => {
    loadProjects();
    const interval = setInterval(() => {
      refreshProjectStatuses();
    }, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleAdd = async (path: string, name?: string) => {
    const success = await addProject(path, name);
    if (success) {
      await loadProjects();
    }
    return success;
  };

  const handleRemove = async (name: string) => {
    const success = await removeProject(name);
    if (success) {
      await loadProjects();
    }
    return success;
  };

  const handleSetActive = async (name: string) => {
    const success = await setActiveProject(name);
    if (success) {
      await loadProjects();
    }
    return success;
  };

  return (
    <div>
      <h1>Projects</h1>
      <ProjectForm onAdd={handleAdd} />
      {loading && <p>Loading projects...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <ProjectList
        projects={projects}
        activeProjectName={activeProjectName || undefined}
        onRemove={handleRemove}
        onSetActive={handleSetActive}
      />
    </div>
  );
};

export default ProjectsPage;
