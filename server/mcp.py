"""
MCP server for Augmentorium
"""

import os
import sys
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Set, Tuple, Union, IO
from queue import Queue

from augmentorium.config.manager import ConfigManager
from augmentorium.utils.db_utils import VectorDB
from augmentorium.server.query import QueryProcessor, RelationshipEnricher, ContextBuilder, QueryExpander, QueryResult
from augmentorium.indexer.embedder import OllamaEmbedder

logger = logging.getLogger(__name__)

class MCPServer:
    """Main server for MCP"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        active_project_path: Optional[str] = None,
        stdin: Optional[IO] = None,
        stdout: Optional[IO] = None
    ):
        """
        Initialize MCP server
        
        Args:
            config_manager: Configuration manager
            active_project_path: Path to the active project
            stdin: Input stream (default: sys.stdin)
            stdout: Output stream (default: sys.stdout)
        """
        self.config_manager = config_manager
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        
        # Set up active project
        self.active_project_path = None
        self.query_processor = None
        self.relationship_enricher = None
        self.context_builder = None
        
        # Set up Ollama embedder
        ollama_config = config_manager.global_config.get("ollama", {})
        self.ollama_embedder = OllamaEmbedder(
            base_url=ollama_config.get("base_url", "http://localhost:11434"),
            model=ollama_config.get("embedding_model", "codellama")
        )
        
        # Initialize with active project if provided
        if active_project_path:
            self.set_active_project(active_project_path)
        else:
            # Try to use the first project in the registry
            projects = config_manager.get_all_projects()
            if projects:
                first_project = list(projects.values())[0]
                self.set_active_project(first_project)
        
        # Set up context builder
        self.context_builder = ContextBuilder(
            max_context_size=config_manager.global_config.get("server", {}).get("max_context_size", 8192)
        )
        
        # Running flag
        self.running = False
        
        logger.info("Initialized MCP server")
    
    def set_active_project(self, project_path: str) -> bool:
        """
        Set the active project
        
        Args:
            project_path: Path to the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project_path = os.path.abspath(project_path)
            
            # Check if project exists
            if not os.path.isdir(project_path):
                logger.error(f"Project directory does not exist: {project_path}")
                return False
            
            # Set active project
            self.active_project_path = project_path
            
            # Get database path
            db_path = self.config_manager.get_db_path(project_path)
            
            # Initialize vector database
            vector_db = VectorDB(db_path)
            
            # Set up query processor
            self.query_processor = QueryProcessor(
                vector_db=vector_db,
                expander=QueryExpander(self.ollama_embedder),
                cache_size=self.config_manager.global_config.get("server", {}).get("cache_size", 100)
            )
            
            # Set up relationship enricher
            self.relationship_enricher = RelationshipEnricher(vector_db)
            
            # Get project name
            project_config = self.config_manager.get_project_config(project_path)
            project_name = project_config["project"]["name"]
            
            logger.info(f"Set active project: {project_name} ({project_path})")
            
            return True
        except Exception as e:
            logger.error(f"Failed to set active project {project_path}: {e}")
            return False
    
    def get_active_project(self) -> Optional[str]:
        """
        Get the active project path
        
        Returns:
            Optional[str]: Path to the active project
        """
        return self.active_project_path
    
    def process_query(
        self,
        query: str,
        n_results: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> Tuple[str, List[QueryResult]]:
        """
        Process a query
        
        Args:
            query: Query text
            n_results: Number of results to return
            min_score: Minimum relevance score
            filters: Filters for metadata
            include_metadata: Whether to include metadata in the context
            
        Returns:
            Tuple[str, List[QueryResult]]: Context and query results
        """
        try:
            if not self.active_project_path or not self.query_processor:
                return "No active project selected.", []
            
            # Process query
            results = self.query_processor.query(
                query_text=query,
                n_results=n_results,
                min_score=min_score,
                filters=filters
            )
            
            # Enrich results with relationship data
            if self.relationship_enricher:
                results = self.relationship_enricher.enrich_results(results)
            
            # Build context
            context = self.context_builder.build_context(
                query=query,
                results=results,
                include_metadata=include_metadata
            )
            
            return context, results
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            return f"Error processing query: {e}", []
    
    def handle_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a command
        
        Args:
            command: Command data
            
        Returns:
            Dict[str, Any]: Response data
        """
        try:
            cmd_type = command.get("type")
            
            if cmd_type == "query":
                # Process query
                query = command.get("query", "")
                n_results = command.get("n_results", 10)
                min_score = command.get("min_score", 0.0)
                filters = command.get("filters")
                include_metadata = command.get("include_metadata", True)
                
                context, results = self.process_query(
                    query=query,
                    n_results=n_results,
                    min_score=min_score,
                    filters=filters,
                    include_metadata=include_metadata
                )
                
                return {
                    "status": "success",
                    "context": context,
                    "results": [result.to_dict() for result in results]
                }
            
            elif cmd_type == "set_project":
                # Set active project
                project_path = command.get("project_path", "")
                
                success = self.set_active_project(project_path)
                
                return {
                    "status": "success" if success else "error",
                    "message": f"Set active project: {project_path}" if success else f"Failed to set active project: {project_path}"
                }
            
            elif cmd_type == "get_project":
                # Get active project
                project_path = self.get_active_project()
                
                return {
                    "status": "success",
                    "project_path": project_path
                }
            
            elif cmd_type == "list_projects":
                # List all projects
                projects = self.config_manager.get_all_projects()
                
                return {
                    "status": "success",
                    "projects": projects
                }
            
            elif cmd_type == "clear_cache":
                # Clear query cache
                if self.query_processor:
                    self.query_processor.clear_cache()
                
                return {
                    "status": "success",
                    "message": "Query cache cleared"
                }
            
            else:
                # Unknown command
                return {
                    "status": "error",
                    "message": f"Unknown command type: {cmd_type}"
                }
        except Exception as e:
            logger.error(f"Failed to handle command: {e}")
            return {
                "status": "error",
                "message": f"Error handling command: {e}"
            }
    
    def run_stdin_stdout(self) -> None:
        """Run the server using stdin/stdout for communication"""
        self.running = True
        
        logger.info("Running MCP server with stdin/stdout")
        
        while self.running:
            try:
                # Read command from stdin
                line = self.stdin.readline()
                
                # Check if stdin is closed
                if not line:
                    logger.info("Stdin closed, stopping server")
                    self.running = False
                    break
                
                # Parse command
                try:
                    command = json.loads(line)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {line}")
                    response = {
                        "status": "error",
                        "message": "Invalid JSON"
                    }
                    self.stdout.write(json.dumps(response) + "\n")
                    self.stdout.flush()
                    continue
                
                # Handle command
                response = self.handle_command(command)
                
                # Write response to stdout
                self.stdout.write(json.dumps(response) + "\n")
                self.stdout.flush()
            except Exception as e:
                logger.error(f"Error in stdin/stdout loop: {e}")
                
                # Send error response
                response = {
                    "status": "error",
                    "message": f"Error in stdin/stdout loop: {e}"
                }
                
                try:
                    self.stdout.write(json.dumps(response) + "\n")
                    self.stdout.flush()
                except:
                    pass
    
    def stop(self) -> None:
        """Stop the server"""
        self.running = False


class MCPService:
    """Service for MCP"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        active_project_path: Optional[str] = None
    ):
        """
        Initialize MCP service
        
        Args:
            config_manager: Configuration manager
            active_project_path: Path to the active project
        """
        self.config_manager = config_manager
        self.active_project_path = active_project_path
        
        # Initialize MCP server
        self.server = MCPServer(
            config_manager=config_manager,
            active_project_path=active_project_path
        )
        
        # Initialize thread
        self.thread = None
        self.running = False
        
        logger.info("Initialized MCP service")
    
    def start(self) -> None:
        """Start the service"""
        if self.running:
            logger.warning("MCP service already running")
            return
        
        logger.info("Starting MCP service")
        
        # Start server in a thread
        self.running = True
        self.thread = threading.Thread(target=self.server.run_stdin_stdout)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the service"""
        if not self.running:
            logger.warning("MCP service not running")
            return
        
        logger.info("Stopping MCP service")
        
        # Stop server
        self.server.stop()
        
        # Wait for thread to exit
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        self.running = False


def start_server(
    config: ConfigManager,
    port: int = 6655,
    active_project: Optional[str] = None
) -> MCPService:
    """
    Start the MCP server
    
    Args:
        config: Configuration manager
        port: Port for the API server
        active_project: Path to the active project
    
    Returns:
        MCPService: MCP service
    """
    # Create MCP service
    service = MCPService(
        config_manager=config,
        active_project_path=active_project
    )
    
    # Start service
    service.start()
    
    return service


def main():
    """Main entry point"""
    from augmentorium.config.manager import ConfigManager
    from augmentorium.utils.logging import setup_logging
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Augmentorium MCP Server")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--project", help="Path to the active project")
    parser.add_argument("--port", type=int, default=6655, help="Port for the API server")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                        help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Start server
    service = start_server(config, args.port, args.project)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping MCP server")
        service.stop()


if __name__ == "__main__":
    main()
