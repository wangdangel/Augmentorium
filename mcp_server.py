#!/usr/bin/env python3
"""
Augmentorium MCP Server
Provides code context to LLMs through the Model Context Protocol
"""

import os
import sys
import json
import logging
import argparse
import time
import asyncio
import urllib.request
import urllib.error
from urllib.parse import urljoin
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import the MCP SDK
try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError:
    print("Error: MCP SDK not found. Install it with 'pip install mcp'")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.augmentorium/logs/mcp_server.log")),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("augmentorium_mcp")

# Default inactivity timeout (seconds)
DEFAULT_TIMEOUT = 300  # 5 minutes

class AugmentoriumMCP:
    """Augmentorium MCP Server implementation"""
    
    def __init__(self, api_url: str, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the MCP server
        
        Args:
            api_url: URL for the Augmentorium API
            timeout: Inactivity timeout in seconds
        """
        self.api_url = api_url
        self.timeout = timeout
        self.last_activity = datetime.now()
        
        # Create MCP server
        self.mcp = FastMCP("Augmentorium Code Context")
        
        # Register tools
        self.register_tools()
        
        # Start inactivity timer
        self.start_inactivity_timer()
    
    def api_request(self, endpoint: str, data: dict) -> dict:
        """Make a request to the Augmentorium API"""
        url = urljoin(self.api_url, endpoint)
        
        try:
            # Convert data to JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Create request
            request = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Make request
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            logger.error(f"API request error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e)}
    
    def register_tools(self):
        """Register MCP tools"""
        
        @self.mcp.tool()
        def query_codebase(query: str) -> str:
            """
            Query the codebase for relevant code given a natural language query
            
            Args:
                query: Natural language query about the codebase
                
            Returns:
                str: Relevant code context
            """
            try:
                self.update_activity()
                logger.info(f"Querying codebase: {query}")
                
                # Call Augmentorium API
                result = self.api_request("/api/query", {"query": query})
                
                if "error" in result:
                    return f"Error querying codebase: {result['error']}"
                
                return result.get("context", "No context found")
            except Exception as e:
                logger.error(f"Error querying codebase: {e}")
                return f"Error querying codebase: {e}"
        
        @self.mcp.tool()
        def get_file_content(file_path: str) -> str:
            """
            Get the content of a specific file
            
            Args:
                file_path: Path to the file
                
            Returns:
                str: File content
            """
            try:
                self.update_activity()
                logger.info(f"Getting file content: {file_path}")
                
                # Call Augmentorium API
                result = self.api_request("/api/file", {"path": file_path})
                
                if "error" in result:
                    return f"Error getting file: {result['error']}"
                
                return result.get("content", f"File not found: {file_path}")
            except Exception as e:
                logger.error(f"Error getting file content: {e}")
                return f"Error getting file content: {e}"
        
        @self.mcp.tool()
        def search_functions(query: str) -> str:
            """
            Search for functions matching a query
            
            Args:
                query: Search query for function name or description
                
            Returns:
                str: Matching functions
            """
            try:
                self.update_activity()
                logger.info(f"Searching functions: {query}")
                
                # Call Augmentorium API
                result = self.api_request("/api/search", {"query": query, "type": "function"})
                
                if "error" in result:
                    return f"Error searching functions: {result['error']}"
                
                return result.get("context", "No functions found")
            except Exception as e:
                logger.error(f"Error searching functions: {e}")
                return f"Error searching functions: {e}"
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.now()
    
    def start_inactivity_timer(self):
        """Start the inactivity timer"""
        async def check_inactivity():
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                idle_time = datetime.now() - self.last_activity
                if idle_time > timedelta(seconds=self.timeout):
                    logger.info(f"Shutting down due to inactivity (idle for {idle_time.total_seconds()}s)")
                    sys.exit(0)
        
        # Start the inactivity checker in the background
        asyncio.create_task(check_inactivity())
    
    async def run(self):
        """Run the MCP server"""
        logger.info(f"Starting Augmentorium MCP Server (API: {self.api_url})")
        await self.mcp.serve()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Augmentorium MCP Server")
    parser.add_argument("--api-url", default="http://localhost:6655", 
                      help="URL for the Augmentorium API")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                      help="Inactivity timeout in seconds")
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.expanduser("~/.augmentorium/logs"), exist_ok=True)
    
    # Start the MCP server
    server = AugmentoriumMCP(api_url=args.api_url, timeout=args.timeout)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())