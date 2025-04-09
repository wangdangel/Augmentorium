# Augmentorium Project Overview

## Project Description

Augmentorium is a code-aware RAG (Retrieval-Augmented Generation) system designed to give LLMs access to full codebases. It continuously monitors, indexes, and embeds code files, allowing LLMs to query and understand entire codebases for better code completion, refactoring suggestions, and insights.

## Architecture

### Core Components

#### 1. Continuous Indexing Service
- **Purpose**: Monitor codebases and update the vector database when files change
- **Key Technologies**: Watchdog, Tree-sitter, Chroma DB, Ollama API
- **Key Features**:
  - File system event monitoring with hash-based change detection
  - Multi-language support via Tree-sitter grammars
  - AST-aware code chunking and relationship detection
  - Project-specific vector databases for portability

#### 2. MCP Server
- **Purpose**: Provide an interface for LLMs to query the codebase
- **Key Technologies**: Standard I/O, REST API, Chroma DB
- **Key Features**:
  - Standard I/O interface for LLM tools like Cursor
  - Query expansion for better retrieval
  - LRU caching for frequent queries
  - Relationship-aware context building
  - Project switching functionality

### Data Flow

1. **Indexing Flow**:
   ```
   File Change → Watchdog → Tree-sitter Parsing → 
   AST-based Chunking → Relationship Detection → 
   Metadata Enrichment → Ollama Embedding → Chroma DB
   ```

2. **Query Flow**:
   ```
   LLM Tool Query → MCP Server → Query Expansion → 
   Vector Search → Relationship Enrichment → 
   Context Building → Response via Standard I/O
   ```

### Project Structure

```
augmentorium/
├── __init__.py
├── app.py                     # Main entry point
├── config/                    # Configuration management
│   ├── __init__.py
│   ├── defaults.py            # Default configuration values
│   └── manager.py             # Configuration manager
├── indexer/                   # Indexing components
│   ├── __init__.py            # Indexer service
│   ├── chunker.py             # Code chunking system
│   ├── embedder.py            # Embedding with Ollama
│   ├── parser.py              # Code parsing with Tree-sitter
│   └── watcher.py             # File system monitoring
├── server/                    # Server components
│   ├── __init__.py            # Server initialization
│   ├── api.py                 # REST API for management
│   ├── mcp.py                 # MCP server (stdin/stdout interface)
│   └── query.py               # Query processing
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── db_utils.py            # Vector database utilities
│   ├── grammar_manager.py     # Tree-sitter grammar management
│   ├── logging.py             # Logging utilities
│   └── path_utils.py          # Path handling utilities
├── scripts/                   # Installation scripts
│   ├── dev/                   # Development scripts
│   │   ├── run_indexer.py     # Run indexer for development
│   │   └── run_server.py      # Run server for development
│   ├── install_linux.sh       # Linux installer
│   ├── install_macos.sh       # macOS installer
│   ├── install_windows.ps1    # Windows installer
│   └── setup_project.py       # Project setup utility
└── tests/                     # Test suite
```

## Development Environment

### Local Setup

For local development, the following steps are recommended:

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate.bat  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

3. **Run the development setup script**:
   ```bash
   python setup_dev.py
   ```

4. **Start the indexer and server**:
   ```bash
   # Start the indexer
   python scripts/dev/run_indexer.py
   
   # Start the server (in another terminal)
   python scripts/dev/run_server.py
   ```

### Development Workflow

1. **Set up a project**:
   ```bash
   python -m augmentorium.scripts.setup_project /path/to/your/codebase
   ```

2. **Test with the example client**:
   ```bash
   python example_client.py --query "How does the file watcher work?"
   ```

3. **Run unit tests**:
   ```bash
   pytest tests/
   ```

## Key Features

### 1. Code-Aware Understanding
- **AST-based Parsing**: Understands code structure, not just text
- **Language-specific Features**: Recognizes functions, classes, imports, etc.
- **Relationship Detection**: Identifies connections between files and components

### 2. Incremental & Intelligent Indexing
- **Change Detection**: Only processes modified files
- **Relationship Tracking**: Maintains cross-references between code units
- **Metadata Enrichment**: Adds file paths, authorship, timestamps, dependencies

### 3. Smart Retrieval
- **Query Expansion**: Improves retrieval by understanding code terms
- **Relationship Context**: Provides connected code units in responses
- **Code-Optimized Context**: Preserves code structure in results

### 4. Developer-Friendly Design
- **Runs Locally**: All processing happens on the developer's machine
- **Tool Integration**: Works with existing LLM coding tools via standard I/O
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Per-Project Databases**: Each codebase has its own vector database

## Integration with LLMs

Augmentorium can be integrated with LLMs in two ways:

1. **Standard I/O Interface**: For direct integration with LLM tools
   ```
   LLM Tool → stdin/stdout → MCP Server → Response
   ```

2. **REST API**: For web or application integrations
   ```
   Application → HTTP → API Server → Response
   ```

The MCP server's context builder creates code-optimized context that preserves the structure and relationships of the code, making it easier for LLMs to understand and work with the codebase.

## Future Work

1. **Dashboard**: A web-based dashboard for monitoring and management
2. **Improved Relationship Detection**: More sophisticated analysis of code relationships
3. **Enhanced Query Expansion**: Better understanding of code terminology
4. **Integration Plugins**: Dedicated plugins for popular LLM tools
5. **Multi-Codebase Support**: Search across multiple projects
