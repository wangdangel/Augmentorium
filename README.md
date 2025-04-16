<!-- Badges and Buy Me a Coffee -->
<p align="center">
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
- [MCP Server Setup (Cline, Roo, Claude Coder, Windsurf, etc.)](#mcp-server-setup-cline-roo-claude-coder-windsurf-etc)
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
- 🤖 **MCP server for agent/LLM integration (Standard IO)**
- 🌐 **Web-based force-graph frontend**
- 🔌 **Pluggable project support**
- 🛡️ **Strict typing and error reporting**
- 📦 **Easy deployment via Supervisor and one-line installers**
- ☕ **[Support the developer!](https://buymeacoffee.com/ambientflare)**

---

## Demo
> _"Augmentorium in action: codebase analysis, graph generation, and agent queries."

![Demo GIF Placeholder](https://via.placeholder.com/800x400?text=Augmentorium+Demo+Coming+Soon)

---

## Installation

### Prerequisites
- [Ollama](https://ollama.com/) (for embeddings, must be installed locally)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/augmentorium.git
cd augmentorium_release
```

### 2. Run the Installer for Your Platform
### Platform Script Permissions & Privileges

> **IMPORTANT:**
> - **Windows:** You must run `setup_augmentorium_windows.bat` as **Administrator**. Right-click the script and select "Run as administrator" to ensure all dependencies and services are installed correctly.
> - **Linux & Mac:** You must run the setup script as **root** (use `sudo`). Before running, make sure the script is executable:
>   ```bash
>   chmod +x setup_augmentorium_linux.sh   # or setup_augmentorium_mac.sh
>   sudo ./setup_augmentorium_linux.sh     # or sudo ./setup_augmentorium_mac.sh
>   ```
> - If you downloaded the script or cloned the repo on Linux/Mac, always check permissions and use `chmod +x` if needed.

These scripts handle all dependency installation, environment setup, and Supervisor configuration. No manual Python environment setup is required.

Choose your platform and run the provided script:
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

---

## Usage

All services (indexer, API server, MCP server, frontend) are automatically managed by Supervisor and the provided installer scripts. **You do not need to manually launch or configure any processes.**

- To start or restart Augmentorium, simply rerun the setup script for your platform.
- Supervisor ensures all components are running and automatically restarts them if needed.

---

## MCP Server Setup (Cline, Roo, Claude Coder, Windsurf, etc.)

The MCP server is implemented in Node.js and communicates via **standard IO** (stdin/stdout). This enables seamless integration with Cline, Roo, Claude Coder, Windsurf, and other MCP-compliant agents.

### How to Add Augmentorium to Your `mcp_config.json`

Add the following chunk to the `tools` section of your `mcp_config.json`:

```json
"augment": {
  "transports": [ "stdio" ],
  "command": "node",
  "args": [
    "c:path_to_install_folder/augmentorium/mcp/dist/mcp-server.js"
  ],
  "cwd": "c:path_to_install_folder/augmentorium/mcp",
  "disabled": false,
  "timeout": 60,
  "autoApprove": [],
  "alwaysAllow": []
}
```

> **Note:**
> - The above paths use Windows-style (`c:path_to_install_folder`). 

## Ollama Embedding Requirements

Augmentorium uses [Ollama](https://ollama.com/) for local embedding generation. **You must have Ollama installed locally** for embedding and semantic search features to work.

- Download and install Ollama from [https://ollama.com/](https://ollama.com/)
- Once installed, embeddings will be available automatically to Augmentorium. No need to run a separate server.

---

## Project Structure
```
augmentorium_release/
├── app.py                  # Main entry point
├── config.yaml             # Main configuration file
├── requirements.txt        # Python dependencies
├── frontend/               # Frontend (web UI)
├── indexer/                # Indexing logic
├── mcp/                    # MCP server (Node.js)
├── scripts/                # Helper scripts
├── server/                 # API server logic
├── utils/                  # Utility modules
├── tests/                  # Test cases
├── setup_augmentorium_*.sh # Setup scripts
├── setup_augmentorium_windows.bat # Windows installer
├── supervisord.conf        # Supervisor config
```

---

## Troubleshooting & FAQ

**Q: The frontend force-graph fails to render or throws errors?**
- Ensure all backend graph data links reference existing nodes (see backend filtering logic).
- Rerun the setup script to ensure all services are running.

**Q: Embeddings are not working?**
- Make sure Ollama is installed locally.
- Rerun the installer if you encounter issues.

**Q: How do I restart all services?**
- Rerun the setup script for your platform.

For more, see the [Issues](https://github.com/YOUR_USERNAME/augmentorium/issues) page.

---

## Contributing

Contributions are welcome! Please open issues, submit PRs, or suggest features.

---

## License

This project is licensed under the MIT License.

---

## Branches & Contributions

> **This is the `release` branch.**
>
> For all development, bug fixes, or new features, please submit pull requests or commits to the `master` branch. The `release` branch is for stable production use only.

---

## Acknowledgments
- [Ollama](https://ollama.com/) for local embeddings
- [Model Context Protocol](https://github.com/modelcontextprotocol) for agent integration
- [Supervisor](http://supervisord.org/) for process management
- [Buy Me a Coffee](https://buymeacoffee.com/ambientflare) supporters

<p align="center"><b>☄️ Made with passion by AmbientFlare ☄️</b></p>
