"""
Project setup script for Augmentorium
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from augmentorium.config.manager import ConfigManager
from augmentorium.utils.logging import setup_logging

logger = logging.getLogger(__name__)

def setup_project(
    project_path: str,
    template_path: Optional[str] = None,
    project_name: Optional[str] = None
) -> bool:
    """
    Set up a project for Augmentorium
    
    Args:
        project_path: Path to the project
        template_path: Path to a config template
        project_name: Optional project name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Setting up project: {project_path}")
        
        # Initialize config manager
        config_manager = ConfigManager()
        
        # Normalize path
        project_path = os.path.abspath(project_path)
        
        # Create project directory if it doesn't exist
        os.makedirs(project_path, exist_ok=True)
        
        # Initialize project with config manager
        success = config_manager.initialize_project(project_path, project_name)
        
        if not success:
            logger.error(f"Failed to initialize project: {project_path}")
            return False
        
        # If template path is provided, load it and use as template
        if template_path:
            try:
                with open(template_path, 'r') as f:
                    template_content = f.read()
                
                # Apply template
                project_config = config_manager.get_project_config(project_path)
                config_path = os.path.join(project_path, ".augmentorium", "config.yaml")
                
                with open(config_path, 'w') as f:
                    f.write(template_content)
                
                logger.info(f"Applied template from {template_path}")
            except Exception as e:
                logger.error(f"Failed to apply template: {e}")
                # Continue anyway, as we've already initialized the project
        
        logger.info(f"Project setup complete: {project_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to set up project: {e}")
        return False


def create_config_template(template_path: str) -> bool:
    """
    Create a config template file
    
    Args:
        template_path: Path to save the template
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from augmentorium.config.defaults import DEFAULT_PROJECT_CONFIG
        import yaml
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        # Write template
        with open(template_path, 'w') as f:
            yaml.dump(DEFAULT_PROJECT_CONFIG, f, default_flow_style=False)
        
        logger.info(f"Created config template: {template_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create config template: {e}")
        return False


def main():
    """Main entry point"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Augmentorium Project Setup")
    parser.add_argument("project_path", help="Path to the project")
    parser.add_argument("--name", help="Project name (defaults to directory name)")
    parser.add_argument("--template", help="Path to config template")
    parser.add_argument("--create-template", help="Create a template at the specified path")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # If creating a template, do that and exit
    if args.create_template:
        success = create_config_template(args.create_template)
        sys.exit(0 if success else 1)
    
    # Setup project
    success = setup_project(args.project_path, args.template, args.name)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
