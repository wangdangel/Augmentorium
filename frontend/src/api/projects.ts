export interface Project {
  name: string;
  path: string;
  status?: string; // e.g., 'active', 'idle', 'indexing'
  size?: number;   // in bytes
  lastIndexed?: string; // ISO timestamp
}

export async function fetchProjects(): Promise<Project[]> {
  try {
    console.log('[fetchProjects] Request: GET /api/projects');
    const res = await fetch('/api/projects/');
    console.log('[fetchProjects] Response status:', res.status);
    if (!res.ok) {
      console.error('[fetchProjects] Failed to fetch projects');
      return [];
    }
    const data = await res.json();
    console.log('[fetchProjects] Response body:', data);
    if (!data || !data.projects) {
      return [];
    }
    if (Array.isArray(data.projects)) {
      return data.projects;
    }
    // If projects is an object/dictionary, convert to array
    if (typeof data.projects === 'object') {
      return Object.entries(data.projects).map(([name, path]) => ({
        name,
        path: path as string,
      }));
    }
    return [];
  } catch (e) {
    console.error('[fetchProjects] Error:', e);
    return [];
  }
}

export async function addProject(path: string, name?: string): Promise<boolean> {
  console.log('[addProject] Request: POST /api/projects', { path, name });
  const res = await fetch('/api/projects/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, name }),
  });
  console.log('[addProject] Response status:', res.status);
  try {
    const data = await res.json();
    console.log('[addProject] Response body:', data);
  } catch (e) {
    console.log('[addProject] No JSON response or error:', e);
  }
  return res.ok;
}

export async function removeProject(name: string): Promise<boolean> {
  console.log('[removeProject] Request: DELETE /api/projects/' + encodeURIComponent(name));
  const res = await fetch(`/api/projects/${encodeURIComponent(name)}/`, {
    method: 'DELETE',
  });
  console.log('[removeProject] Response status:', res.status);
  try {
    const data = await res.json();
    console.log('[removeProject] Response body:', data);
  } catch (e) {
    console.log('[removeProject] No JSON response or error:', e);
  }
  return res.ok;
}

export async function getActiveProject(): Promise<Project | null> {
  try {
    console.log('[getActiveProject] Request: GET /api/projects/active');
    const res = await fetch('/api/projects/active');
    console.log('[getActiveProject] Response status:', res.status);
    if (!res.ok) return null;
    const data = await res.json();
    console.log('[getActiveProject] Response body:', data);
    return data.project || null;
  } catch (e) {
    console.error('[getActiveProject] Error:', e);
    return null;
  }
}

export async function setActiveProject(name: string): Promise<boolean> {
  try {
    console.log('[setActiveProject] Request: POST /api/projects/active', { name });
    const res = await fetch('/api/projects/active', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    console.log('[setActiveProject] Response status:', res.status);
    try {
      const data = await res.json();
      console.log('[setActiveProject] Response body:', data);
    } catch (e) {
      console.log('[setActiveProject] No JSON response or error:', e);
    }
    return res.ok;
  } catch (e) {
    console.error('[setActiveProject] Error:', e);
    return false;
  }
}

export async function reindexSpecificProject(projectName: string): Promise<boolean> {
  console.log('[reindexSpecificProject] Request: POST /api/projects/' + encodeURIComponent(projectName) + '/reindex');
  const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/reindex`, {
    method: 'POST',
  });
  console.log('[reindexSpecificProject] Response status:', res.status);
  try {
    const data = await res.json();
    console.log('[reindexSpecificProject] Response body:', data);
  } catch (e) {
    console.log('[reindexSpecificProject] No JSON response or error:', e);
  }
  return res.ok;
}
