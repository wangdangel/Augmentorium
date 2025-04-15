import requests
import json

BASE_URL = "http://localhost:6655"

# Utility to get a valid project name for endpoints that require it
try:
    projects_resp = requests.get(BASE_URL + "/api/projects/")
    projects = projects_resp.json().get("projects", []) if projects_resp.status_code == 200 else []
    project_name = projects[0]["name"] if projects else None
except Exception:
    project_name = None

endpoints = [
    ("GET", "/api/health/", None),
    ("GET", "/api/indexer/", None),
    ("GET", "/api/indexer/status", None),
    ("POST", "/api/indexer/status", {"projects": []}),
    ("GET", "/api/graph/", None),
    ("GET", "/api/cache/", None),
    ("DELETE", "/api/cache/", None),
    ("POST", "/api/query/", {"query": "test"}),
    ("DELETE", "/api/query/cache", None),
    ("GET", "/api/projects/", None),
    ("GET", "/api/projects/active", None),
    ("POST", "/api/projects/", {"path": "dummy_path"}),
    # New project-aware endpoints:
    ("GET", f"/api/files/?project={project_name}" if project_name else "/api/files/", None),
    ("POST", "/api/chunks/search", {"query": "def foo", "project": project_name} if project_name else {"query": "def foo"}),
    ("POST", "/api/graph/neighbors/", {"node_id": "dummy", "project": project_name} if project_name else {"node_id": "dummy"}),
    ("POST", "/api/explain", {"query": "explain this", "project": project_name} if project_name else {"query": "explain this"}),
    ("GET", f"/api/stats/?project={project_name}" if project_name else "/api/stats/", None),
    ("GET", f"/api/health/llm_window/?project={project_name}" if project_name else "/api/health/llm_window/", None),
]

# Add new endpoints for MCP query and graph neighbors
endpoints.extend([
    ("POST", "/api/query/mcp/", {"project": project_name, "query": "test MCP query"} if project_name else {"query": "test MCP query"}),
    ("POST", "/api/graph/neighbors/", {"project": project_name, "node_id": "dummy_node_id"} if project_name else {"node_id": "dummy_node_id"}),
])

# Run a query to get a real result for /api/explain
explain_result = None
try:
    resp = requests.post(BASE_URL + "/api/query/", json={"query": "test"})
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and "results" in data and data["results"]:
            explain_result = data["results"][0]
except Exception:
    pass

# Update /api/explain endpoint with a real result if available
for i, (method, path, payload) in enumerate(endpoints):
    if path.startswith("/api/explain"):
        endpoints[i] = (method, path, {"query": "test", "project": project_name, "result": explain_result} if explain_result else {"query": "test", "project": project_name})

results = []

for method, path, payload in endpoints:
    url = BASE_URL + path
    try:
        if method == "GET":
            resp = requests.get(url)
        elif method == "POST":
            resp = requests.post(url, json=payload)
        elif method == "DELETE":
            resp = requests.delete(url)
        else:
            results.append({"endpoint": path, "error": f"Unsupported method {method}"})
            continue
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        results.append({
            "method": method,
            "endpoint": path,
            "status_code": resp.status_code,
            "response": data
        })
    except Exception as e:
        results.append({"method": method, "endpoint": path, "error": str(e)})

with open("api_endpoint_responses.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("Results saved to api_endpoint_responses.json")
