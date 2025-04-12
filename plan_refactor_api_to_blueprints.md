# Refactor Plan: Modularize `server/api.py` Using Flask Blueprints

## Objective

Refactor the monolithic `server/api.py` into modular API groups using Flask Blueprints. This will improve maintainability, enable parallel development, and make the codebase more scalable.

---

## 1. Proposed Directory Structure

```
server/
  api/
    __init__.py
    api_health.py
    api_projects.py
    api_documents.py
    api_query.py
    api_graph.py
    api_cache.py
    api_indexer.py
    common.py         # Shared decorators/utilities
  api.py              # Orchestrator: registers all Blueprints
```

---

## 2. Migration Steps

### Step 1: Create the `server/api/` Directory

- Move all API-related code into this directory.
- Add an empty `__init__.py` to make it a package.

### Step 2: Split Endpoints by Group

- For each logical group (projects, documents, query, etc.), create a new file (e.g., `api_projects.py`).
- In each file, define a Flask Blueprint and move the relevant endpoints into it.

**Example: `api_projects.py`**
```python
from flask import Blueprint, request, jsonify, Response
projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

@projects_bp.route('', methods=['GET'])
def get_projects():
    # ...implementation...
    pass

@projects_bp.route('', methods=['POST'])
def add_project():
    # ...implementation...
    pass

# ...other project-related endpoints...
```

### Step 3: Move Shared Utilities

- Move shared decorators (e.g., `require_active_project`) and helpers to `common.py`.
- Import them in each Blueprint module as needed.

### Step 4: Register Blueprints in `api.py`

- In `server/api.py`, import and register all Blueprints with the Flask app.

**Example:**
```python
from flask import Flask
from server.api.api_projects import projects_bp
from server.api.api_documents import documents_bp
# ...other imports...

def create_app():
    app = Flask("augmentorium")
    app.register_blueprint(projects_bp)
    app.register_blueprint(documents_bp)
    # ...register other blueprints...
    return app
```

### Step 5: Update Server Initialization

- Update any code that creates the Flask app to use the new `create_app()` function.

### Step 6: Update Tests

- Update imports in tests to use the new Blueprint structure.

---

## 3. Mermaid Diagram

```mermaid
flowchart TD
    A[api.py (orchestrator)] --> B1[api/api_projects.py]
    A --> B2[api/api_documents.py]
    A --> B3[api/api_query.py]
    A --> B4[api/api_graph.py]
    A --> B5[api/api_cache.py]
    A --> B6[api/api_health.py]
    A --> B7[api/api_indexer.py]
    B1 -.-> C[api/common.py (decorators, utils)]
    B2 -.-> C
    B3 -.-> C
    B4 -.-> C
    B5 -.-> C
    B6 -.-> C
    B7 -.-> C
```

---

## 4. Benefits

- **Separation of concerns:** Each API group is isolated.
- **Parallel development:** Multiple contributors can work on different API modules.
- **Scalability:** New endpoints can be added as new Blueprints.
- **Maintainability:** Smaller, focused files are easier to test and debug.

---

## 5. Next Steps

- Confirm this plan.
- Begin implementation by creating the new directory and moving endpoints into Blueprints.