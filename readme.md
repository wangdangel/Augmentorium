# Augmentorium

A code-aware RAG (Retrieval Augmented Generation) system for LLM access to codebases.

## Overview

Augmentorium continuously monitors, indexes, and embeds your code files, allowing LLMs to query and understand entire codebases for better code completion, refactoring suggestions, and insights.

### Key Features

- **Continuous Code Indexing**: Monitors file changes and automatically updates the knowledge base
- **AST-Aware Parsing**: Understands code structure, not just text
- **Language Support**: Python, JavaScript, TypeScript, and more
- **Relationship Detection**: Identifies connections between code components
- **Runs 100% Locally**: All processing happens on your machine
- **LLM Integration**: Standard I/O interface for easy integration with any LLM

## Quick Start

### Prerequisites

- Python 3.8 or newer
- Git
- Ollama running locally (for embeddings)

### Installation for Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/augmentorium.git
   cd augmentorium
   ```

2. Run the development setup script:
   ```bash
   python setup_dev.py
   ```

3. Start the indexer:
   ```bash
   # On Linux/macOS
   scripts/dev/run_indexer.sh
   
   # On Windows
   scripts/dev/run_indexer.bat
   ```

4. Start the MCP server:
   ```bash
   # On Linux/macOS
   scripts/dev/run_server.sh
   
   # On Windows
   scripts/dev/run_server.bat
   ```

### Setting Up a Project

To index a codebase:

```bash
# Activate the virtual environment
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate.bat  # Windows

# Set up a project
python -m augmentorium.scripts.setup_project /path/to/your/codebase
```

## Project Structure

- `augmentorium/`: Main package
  - `config/`: Configuration management
  - `indexer/`: Code indexing components
  - `server/`: MCP server components
  - `utils/`: Utility modules
- `scripts/`: Installation and utility scripts
- `dashboard/`: Web dashboard (optional)
- `tests/`: Test suite

## Components

### Indexer Service

The indexer continuously monitors your codebase and updates the vector database when files change:

1. Detects file changes using Watchdog
2. Parses code using Tree-sitter
3. Chunks code into semantic units
4. Embeds chunks via Ollama
5. Stores in vector database (ChromaDB)

### MCP Server

The MCP (Main Control Program) server handles queries from LLMs:

1. Receives queries via standard I/O or REST API
2. Expands and processes queries
3. Retrieves relevant code from vector database
4. Enriches results with relationship data
5. Builds context for LLM consumption
6. Returns context via standard I/O

## Configuration

Augmentorium uses YAML configuration files:

- Global config: `~/.augmentorium/global_config.yaml`
- Project config: `/path/to/project/.augmentorium/config.yaml`

## License

MIT
