#!/usr/bin/env python3
"""
Example client for Augmentorium MCP Server
This simulates an LLM tool querying Augmentorium
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

def query_mcp_stdin_stdout(query, mcp_command, n_results=10, min_score=0.0):
    """
    Query the MCP server using stdin/stdout
    
    Args:
        query: Query text
        mcp_command: Command to start the MCP server
        n_results: Number of results to return
        min_score: Minimum score threshold
        
    Returns:
        dict: Response from MCP server
    """
    # Prepare the query command
    command = {
        "type": "query",
        "query": query,
        "n_results": n_results,
        "min_score": min_score
    }
    
    # Convert to JSON
    command_json = json.dumps(command)
    
    # Start the MCP server process
    process = subprocess.Popen(
        mcp_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send the command
    stdout, stderr = process.communicate(command_json + "\n")
    
    # Process the response
    if stderr:
        print("Error:", stderr)
        return None
    
    # Parse the JSON response
    try:
        response = json.loads(stdout.strip())
        return response
    except json.JSONDecodeError:
        print("Failed to parse response:", stdout)
        return None

def query_mcp_api(query, host="localhost", port=8080, n_results=10, min_score=0.0):
    """
    Query the MCP server using the REST API
    
    Args:
        query: Query text
        host: API server host
        port: API server port
        n_results: Number of results to return
        min_score: Minimum score threshold
        
    Returns:
        dict: Response from MCP server
    """
    try:
        import requests
    except ImportError:
        print("Please install requests: pip install requests")
        return None
    
    # Prepare the query command
    data = {
        "query": query,
        "n_results": n_results,
        "min_score": min_score
    }
    
    # Send the request
    try:
        response = requests.post(
            f"http://{host}:{port}/api/query",
            json=data
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Example client for Augmentorium MCP Server")
    parser.add_argument("--query", required=True, help="Query text")
    parser.add_argument("--method", choices=["api", "stdin"], default="api", 
                      help="Method to query the MCP server")
    parser.add_argument("--host", default="localhost", help="API server host")
    parser.add_argument("--port", type=int, default=8080, help="API server port")
    parser.add_argument("--n-results", type=int, default=10, help="Number of results to return")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum score threshold")
    parser.add_argument("--mcp-command", default="augmentorium-server", 
                      help="Command to start the MCP server (for stdin method)")
    args = parser.parse_args()
    
    # Query the MCP server
    if args.method == "api":
        response = query_mcp_api(
            query=args.query,
            host=args.host,
            port=args.port,
            n_results=args.n_results,
            min_score=args.min_score
        )
    else:
        response = query_mcp_stdin_stdout(
            query=args.query,
            mcp_command=[args.mcp_command],
            n_results=args.n_results,
            min_score=args.min_score
        )
    
    # Print the response
    if response:
        if "context" in response:
            print("\n=== CONTEXT ===")
            print(response["context"])
        
        if "results" in response:
            print("\n=== RESULTS ===")
            for i, result in enumerate(response["results"]):
                print(f"Result {i+1} - Score: {result['score']:.4f}")
                print(f"File: {result['file_path']}")
                print(f"Type: {result['metadata'].get('chunk_type', 'unknown')}")
                print("-" * 40)
    
    else:
        print("No response or error occurred")

if __name__ == "__main__":
    main()
