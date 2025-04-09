#!/usr/bin/env python3
"""
Augmentorium: Main application entry point
"""

import argparse
import os
import sys
import logging
from config.manager import ConfigManager
from indexer.indexer_init import start_indexer
from server.mcp import start_server
from utils.logging import setup_logging

def main():
    """Main entry point for the Augmentorium application"""
    parser = argparse.ArgumentParser(description="Augmentorium: Code-aware RAG system")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Indexer command
    indexer_parser = subparsers.add_parser("indexer", help="Start the indexing service")
    indexer_parser.add_argument("--config", help="Path to config file")
    indexer_parser.add_argument("--projects", help="Comma-separated list of project paths to monitor")
    indexer_parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                           help="Set the logging level")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the MCP server")
    server_parser.add_argument("--config", help="Path to config file")
    server_parser.add_argument("--project", help="Path to the initial active project")
    server_parser.add_argument("--port", type=int, default=6655, help="Port for the API server")
    server_parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                          help="Set the logging level")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up a project for monitoring")
    setup_parser.add_argument("project_path", help="Path to the project to set up")
    setup_parser.add_argument("--config", help="Path to config file template")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level if hasattr(args, 'log_level') else "INFO")
    setup_logging(log_level)
    
    # Load configuration
    config_path = args.config if hasattr(args, 'config') and args.config else None
    config = ConfigManager(config_path)
    
    # Execute command
    if args.command == "indexer":
        project_paths = args.projects.split(",") if args.projects else None
        start_indexer(config, project_paths)
    elif args.command == "server":
        start_server(config, args.port, args.project)
    elif args.command == "setup":
        from scripts.setup_project import setup_project
        template_path = args.config if hasattr(args, 'config') and args.config else None
        setup_project(args.project_path, template_path)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
