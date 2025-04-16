# Helper functions for project-based backend object selection

def get_project_path(config_manager, project_name):
    """Safely get the project path for a given project name."""
    if not config_manager or not project_name:
        return None
    return config_manager.get_project_path(project_name)

# Add more helpers here for project-specific query processor, graph DB, etc. as needed.
