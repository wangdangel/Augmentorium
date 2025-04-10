#!/usr/bin/env python3
"""
Standalone script to set up a project for Augmentorium
"""

import os
import sys
import logging
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from the augmentorium package
from config.manager import ConfigManager
from utils.logging import setup_logging

def main():
    """Main entry point for setting up a project"""
    parser = argparse.ArgumentParser(description="Augmentorium Project Setup")
    parser.add_argument("project_path", help="Path to the project")
    parser.add_argument("--name", help="Project name (defaults to directory name)")
    parser.add_argument("--template", help="Path to config template")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                      default="INFO", help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.info(f"Setting up project: {args.project_path}")
    
    # Set up project
    config_manager = ConfigManager()
    success = config_manager.initialize_project(args.project_path, args.name)
    
    if success:
        # Additional setup: create .augmentorium and initialize graph DB
        try:
            project_root = os.path.abspath(args.project_path)
            augmentorium_dir = os.path.join(project_root, ".augmentorium")
            os.makedirs(augmentorium_dir, exist_ok=True)

            # Vector DB directory (if not already created)
            vector_db_dir = os.path.join(augmentorium_dir, "chroma_db")
            os.makedirs(vector_db_dir, exist_ok=True)

            # Graph DB file
            graph_db_path = os.path.join(augmentorium_dir, "code_graph.db")
            if not os.path.exists(graph_db_path):
                import sqlite3
                conn = sqlite3.connect(graph_db_path)
                c = conn.cursor()
                c.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    name TEXT,
                    file_path TEXT,
                    start_line INTEGER,
                    end_line INTEGER,
                    metadata TEXT
                )
                """)
                c.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT,
                    target_id TEXT,
                    relation_type TEXT,
                    metadata TEXT
                )
                """)
                c.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)")
                conn.commit()
                conn.close()
                logger.info(f"Graph database initialized at {graph_db_path}")
        except Exception as e:
            logger.warning(f"Failed to initialize .augmentorium or graph DB: {e}")

        logger.info("Project setup complete!")
        print(f"Project setup complete: {args.project_path}")
        print("You can now run the indexer and server to index and query this project.")
    else:
        logger.error("Project setup failed!")
        print("Project setup failed. Check the logs for more information.")
        sys.exit(1)

if __name__ == "__main__":
    main()
