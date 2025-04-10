export interface Project {
  name: string;
  path: string;
  status?: string; // e.g., 'active', 'idle', 'indexing'
  size?: number;   // in bytes
  lastIndexed?: string; // ISO timestamp
}

export async function fetchProjects(): Promise<Project[]> {
  try {
    const res = await fetch('/api/projects');
    if (!res.ok) {
      console.error('Failed to fetch projects');
      return [];
    }
    const data = await res.json();
    if (!data || !Array.isArray(data.projects)) {
      return [];
    }
    return data.projects;
  } catch (e) {
    console.error('Error fetching projects:', e);
    return [];
  }
}

export async function addProject(path: string, name?: string): Promise<boolean> {
  const res = await fetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, name }),
  });
  return res.ok;
}

export async function removeProject(name: string): Promise<boolean> {
  const res = await fetch(`/api/projects/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  });
  return res.ok;
}

export async function getActiveProject(): Promise<Project | null> {
  try {
    const res = await fetch('/api/projects/active');
    if (!res.ok) return null;
    const data = await res.json();
    return data.project || null;
  } catch {
    return null;
  }
}

export async function setActiveProject(path: string): Promise<boolean> {
  try {
    const res = await fetch('/api/projects/active', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    return res.ok;
  } catch {
    return false;
  }
}
