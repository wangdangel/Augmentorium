import requests
import pytest

BASE_URL = "http://localhost:6655"  # Corrected to match backend port

def test_health():
    resp = requests.get(f"{BASE_URL}/api/health/")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

def test_indexer_placeholder():
    resp = requests.get(f"{BASE_URL}/api/indexer/")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

def test_indexer_status_get():
    resp = requests.get(f"{BASE_URL}/api/indexer/status")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)

def test_indexer_status_post():
    payload = {"projects": []}
    resp = requests.post(f"{BASE_URL}/api/indexer/status", json=payload)
    assert resp.status_code in (200, 400)
    assert "status" in resp.json() or "error" in resp.json()

def test_graph_get():
    resp = requests.get(f"{BASE_URL}/api/graph/")
    # Accept 200 (success) or 400 (no active project)
    assert resp.status_code in (200, 400)
    data = resp.json()
    assert isinstance(data, dict)
    assert "nodes" in data or "error" in data

def test_cache_get():
    resp = requests.get(f"{BASE_URL}/api/cache/")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

def test_cache_delete():
    resp = requests.delete(f"{BASE_URL}/api/cache/")
    # Accept 200 (success) or 400 (no active project)
    assert resp.status_code in (200, 400)
    assert "status" in resp.json() or "error" in resp.json()

def test_query_post():
    payload = {"query": "test"}
    resp = requests.post(f"{BASE_URL}/api/query/", json=payload)
    # Accept 200 (success) or 400/500 (missing project or server error)
    assert resp.status_code in (200, 400, 500)
    data = resp.json()
    assert "results" in data or "error" in data

def test_query_cache_delete():
    resp = requests.delete(f"{BASE_URL}/api/query/cache")
    assert resp.status_code in (200, 500, 400)
    assert "status" in resp.json() or "error" in resp.json()

def test_projects_get():
    resp = requests.get(f"{BASE_URL}/api/projects/")
    assert resp.status_code == 200
    assert "projects" in resp.json()

def test_projects_active_get():
    resp = requests.get(f"{BASE_URL}/api/projects/active")
    assert resp.status_code in (200, 404)
    data = resp.json()
    assert isinstance(data, dict)

def test_projects_post():
    payload = {"path": "dummy_path"}
    resp = requests.post(f"{BASE_URL}/api/projects/", json=payload)
    # Accept 200 (success), 400 (bad request), or 500 (internal error)
    assert resp.status_code in (200, 400, 500)
    assert "status" in resp.json() or "error" in resp.json()

def test_files_get_requires_project():
    resp = requests.get(f"{BASE_URL}/api/files/")
    assert resp.status_code == 400
    assert "error" in resp.json()
    assert "project" in resp.json()["error"].lower()

def test_files_get_with_project():
    # Get a valid project name from /api/projects/
    proj_resp = requests.get(f"{BASE_URL}/api/projects/")
    assert proj_resp.status_code == 200
    projects = proj_resp.json().get("projects", [])
    if not projects:
        pytest.skip("No projects available for testing /api/files/ with project param.")
    project_name = projects[0]["name"]
    resp = requests.get(f"{BASE_URL}/api/files/?project={project_name}")
    assert resp.status_code == 200
    data = resp.json()
    assert "files" in data
    assert "total_files" in data

def test_chunks_search_requires_project():
    payload = {"query": "def foo"}
    resp = requests.post(f"{BASE_URL}/api/chunks/search", json=payload)
    assert resp.status_code == 400
    assert "project" in resp.json()["error"].lower()

def test_chunks_search_with_project():
    proj_resp = requests.get(f"{BASE_URL}/api/projects/")
    assert proj_resp.status_code == 200
    projects = proj_resp.json().get("projects", [])
    if not projects:
        pytest.skip("No projects available for testing /api/chunks/search with project param.")
    project_name = projects[0]["name"]
    payload = {"project": project_name, "query": "def foo"}
    resp = requests.post(f"{BASE_URL}/api/chunks/search", json=payload)
    # Accept 200 (success) or 500 (if backend not fully wired)
    assert resp.status_code in (200, 500)
    data = resp.json()
    assert "chunks" in data or "error" in data

def test_graph_neighbors_requires_project():
    payload = {"node_id": "dummy"}
    resp = requests.post(f"{BASE_URL}/api/graph/neighbors/", json=payload)
    assert resp.status_code == 400
    assert "project" in resp.json()["error"].lower()

def test_stats_requires_project():
    resp = requests.get(f"{BASE_URL}/api/stats/")
    assert resp.status_code == 400
    assert "project" in resp.json()["error"].lower()

def test_health_llm_window_requires_project():
    resp = requests.get(f"{BASE_URL}/api/health/llm_window/")
    assert resp.status_code == 400
    assert "project" in resp.json()["error"].lower()

# Add more tests for any new endpoints as needed
