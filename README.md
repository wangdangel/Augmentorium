<!-- Badges and Buy Me a Coffee -->
<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/build-passing-brightgreen.svg" alt="Build Status">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/contributions-welcome-orange.svg" alt="Contributions">
  <a href="https://buymeacoffee.com/ambientflare"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support%20me-yellow?logo=buy-me-a-coffee&logoColor=white" alt="Buy Me a Coffee"></a>
</p>

<h1 align="center">☄️ Augmentorium ☄️</h1>
<p align="center"><b>Code-aware RAG platform for next-gen AI workflows</b></p>

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [MCP Server Setup (Klein Claude AI Windsurf)](#mcp-server-setup-klein-claude-ai-windsurf)
- [Ollama Embedding Requirements](#ollama-embedding-requirements)
- [Project Structure](#project-structure)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview
Augmentorium is a powerful, modular, and extensible Retrieval-Augmented Generation (RAG) platform designed for AI-driven code understanding, project analysis, and knowledge graph workflows. It seamlessly integrates code indexing, context-aware search, and advanced AI agents using the Model Context Protocol (MCP).

Augmentorium is built for:
- Codebase semantic search and RAG
- AI agent orchestration (Claude, Klein Claude, GPT, etc.)
- Knowledge graph generation and visualization
- Multi-project and multi-modal workflows

---

## Features
- ⚡ **Fast, concurrent code indexing**
- 🔎 **Semantic search over code and docs**
- 🧠 **Knowledge graph construction**
- 🤖 **MCP server for agent/LLM integration**
- 🌐 **Web-based force-graph frontend**
- 🔌 **Pluggable project support**
- 🛡️ **Strict typing and error reporting**
- 📦 **Easy deployment via Supervisor**
- ☕ **[Support the developer!](https://buymeacoffee.com/ambientflare)**

---

## Demo
> _"Augmentorium in action: codebase analysis, graph generation, and agent queries."

![Demo GIF Placeholder](https://via.placeholder.com/800x400?text=Augmentorium+Demo+Coming+Soon)

---

## Installation

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com/) running locally for embedding support
- Node.js (for frontend builds, if you wish to modify the frontend)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/augmentorium.git
cd augmentorium_release
```

### 2. Set Up Python Environment
```bash
python -m venv .venv
.venv/Scripts/activate  # On Windows
# Or: source .venv/bin/activate  # On Linux/Mac
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. (Optional) Install Frontend Dependencies
If you wish to modify or rebuild the frontend:
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Install MCP Server Dependencies
```bash
cd mcp
pip install -r requirements.txt
cd ..
```

### 5. (Optional) Install Supervisor
Supervisor is used for process management:
```bash
pip install supervisor
```

---

## Quick Start

### Using Provided Setup Scripts
Run the setup script for your OS:
- **Windows:**
  ```bash
  setup_augmentorium_windows.bat
  ```
- **Linux:**
  ```bash
  bash setup_augmentorium_linux.sh
  ```
- **Mac:**
  ```bash
  bash setup_augmentorium_mac.sh
  ```

### Manual Launch
- **Start the Indexer:**
  ```bash
  python app.py indexer --config config.yaml --projects "<project1>,<project2>"
  ```
- **Start the API Server:**
  ```bash
  python app.py server --config config.yaml --port 6655
  ```
- **Start the MCP Server:**
  ```bash
  cd mcp
  python mcp_server.py
  ```

- **Start the Frontend (if needed):**
  ```bash
  cd frontend/dist
  python -m http.server 6656
  ```

- **(Recommended) Use Supervisor:**
  ```bash
  supervisord -c supervisord.conf
  ```

---

## Usage

### Indexing Projects
To index one or more projects:
```bash
python app.py indexer --config config.yaml --projects "K:\\Documents\\icecrawl,K:\\Documents\\alphaone"
```

### Running the API Server
```bash
python app.py server --config config.yaml --port 6655
```

### Accessing the Frontend
Open your browser to [http://localhost:6656](http://localhost:6656)

### Using the MCP Server
```bash
cd mcp
python mcp_server.py  # SSE endpoints
python stdio_server.py  # For CLI/agent integration
```

See `mcp/README.md` for full protocol and endpoint details.

---

## MCP Server Setup (Klein Claude AI Windsurf)

The MCP server enables integration with Klein Claude AI Windsurf and other MCP-compliant agents.

### Steps:
1. **Install MCP dependencies:**
    ```bash
    cd mcp
    pip install -r requirements.txt
    ```
2. **Launch the MCP server:**
    ```bash
    python mcp_server.py  # For SSE endpoints
    # or
    python stdio_server.py  # For CLI/LLM agent integration
    ```
3. **Configure Klein Claude AI Windsurf:**
    - Set the MCP server endpoint to `http://localhost:6655/sse/` (or your chosen port)
    - Ensure the Augmentorium API server is running on the same port
    - For advanced usage, see the [MCP documentation](https://github.com/modelcontextprotocol)

### Notes
- The MCP server only exposes SSE and stdio endpoints (no standard HTTP REST for tool/resource invocation).
- All tools and resources are discoverable via `/sse/tools/` and `/sse/resources/`.
- For LLM/agent integration, always use SSE or stdio transports.

---

## Ollama Embedding Requirements

Augmentorium uses [Ollama](https://ollama.com/) for local embedding generation. **You must have Ollama running locally** for embedding and semantic search features to work.

- Download and install Ollama from [https://ollama.com/](https://ollama.com/)
- Start Ollama before launching Augmentorium:
  ```bash
  ollama serve
  ```
- By default, Augmentorium expects Ollama at `http://localhost:11434` (configurable via `--ollama-url`)

---

## Project Structure
```
augmentorium_release/
├── app.py                  # Main entry point
├── config.yaml             # Main configuration file
├── requirements.txt        # Python dependencies
├── frontend/               # Frontend (web UI)
├── indexer/                # Indexing logic
├── mcp/                    # MCP server (AI agent bridge)
├── scripts/                # Helper scripts
├── server/                 # API server logic
├── utils/                  # Utility modules
├── tests/                  # Test cases
├── setup_augmentorium_*.sh # Setup scripts
├── supervisord.conf        # Supervisor config
```

---

## Troubleshooting & FAQ

**Q: The frontend force-graph fails to render or throws errors?**
- Ensure all backend graph data links reference existing nodes (see backend filtering logic).
- Check that the API server and MCP server are both running.

**Q: Embeddings are not working?**
- Make sure Ollama is installed and running locally (`ollama serve`).
- Check the Ollama API URL in your config or launch command.

**Q: How do I add a new project for indexing?**
- Use the setup command:
  ```bash
  python app.py setup <project_path>
  ```

**Q: How do I restart all services?**
- Use Supervisor: `supervisord -c supervisord.conf`

For more, see the [Issues](https://github.com/YOUR_USERNAME/augmentorium/issues) page.

---

## Contributing

Contributions are welcome! Please open issues, submit PRs, or suggest features.

---

## License

This project is licensed under the MIT License.

---

## Acknowledgments
- [Ollama](https://ollama.com/) for local embeddings
- [Model Context Protocol](https://github.com/modelcontextprotocol) for agent integration
- [Supervisor](http://supervisord.org/) for process management
- [Buy Me a Coffee](https://buymeacoffee.com/ambientflare) supporters

<p align="center"><b>☄️ Made with passion by AmbientFlare ☄️</b></p>
