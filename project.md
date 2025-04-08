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
│   ├── install_linux.sh       # Linux installer
│   ├── install_macos.sh       # macOS installer
│   ├── install_windows.ps1    # Windows installer
│   ├── manage_grammars.py     # Grammar management CLI
│   └── setup_project.py       # Project setup utility
└── tests/                     # Test suite (to be implemented)
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

## Use Cases

1. **Code Comprehension**: Help developers understand unfamiliar codebases
2. **Refactoring Assistance**: Identify dependencies and impact of changes
3. **Documentation Generation**: Create documentation from code comments and structure
4. **Bug Detection**: Find related code patterns across the codebase
5. **Knowledge Preservation**: Maintain institutional knowledge about the codebase

## Deployment Strategy

### Development Environment
- Run as Python modules with hot reloading
- Local embedded Chroma DB
- Console logging for debugging

### Production Environment
- Run as system services (systemd/launchd/Windows Service)
- File-based logging
- Automatic startup on system boot

## Future Roadmap

### Short-term
1. Complete testing suite and documentation
2. Add additional language support
3. Optimize embedding and retrieval performance
4. Create example configurations and templates

### Medium-term
1. Build visualization tools for code relationships
2. Add semantic search improvements
3. Implement version tracking and diff analysis
4. Develop dedicated LLM integration plugins

### Long-term
1. Add support for distributed codebases
2. Implement collaborative features
3. Build a web interface for management
4. Create a hosted service option
