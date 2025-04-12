# Plan to Fix AttributeError in Server Startup

## Problem Summary
- The server fails to start because `build_project_db_mapping` expects `config_manager` to have a `get_projects()` method returning a list of dicts, but `ConfigManager` only provides `get_all_projects()`, which returns a dict of `{name: path}`.
- This mismatch causes an `AttributeError`.

## Solution Overview
- Update `build_project_db_mapping` to use `get_all_projects()` and convert its output to the expected list of dicts.

## Step-by-Step Plan

1. **Update `build_project_db_mapping`:**
   - Replace the call to `config_manager.get_projects()` with a list comprehension that transforms the output of `config_manager.get_all_projects()` into a list of dicts with `'name'` and `'path'` keys:
     ```python
     projects = [{"name": name, "path": path} for name, path in config_manager.get_all_projects().items()]
     ```

2. **Verify Compatibility:**
   - Ensure the rest of `build_project_db_mapping` works with the new structure.
   - No changes needed to `ConfigManager` or other code.

3. **(Optional) Update Documentation:**
   - Update the docstring in `build_project_db_mapping` to clarify that it expects `config_manager` to provide `get_all_projects()`.

---

## Data Flow Diagram (Mermaid)

```mermaid
flowchart TD
    A[ConfigManager] -- get_all_projects() --> B{{Dict: {name: path}}}
    B -- list comprehension --> C[[List of dicts: {"name", "path"}]]
    C -- for project in projects --> D[build_project_db_mapping]
    D -- mapping --> E[Project DB Mapping]
```

---

## Next Steps

- Switch to code mode to implement the fix in `utils/project_db_mapping.py`.