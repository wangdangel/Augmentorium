import React, { useEffect, useState } from 'react';
import { fetchProjects, addProject, removeProject, Project } from '../api/projects';
import ProjectForm from '../components/ProjectForm';
import ProjectList from '../components/ProjectList';

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch (e) {
      console.error(e);
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
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
    await loadProjects(); // Always refresh after delete completes
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
        onRemove={handleRemove}
      />
    </div>
  );
};

export default ProjectsPage;
