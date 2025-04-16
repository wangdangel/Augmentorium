<!-- Badges and Buy Me a Coffee -->
<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen.svg" alt="Build Status">
  <img src="https://img.shields.io/badge/license-PolyForm%20Noncommercial-blueviolet.svg" alt="License: PolyForm Noncommercial">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue.svg" alt="Python 3.8+ Required">
  <img src="https://img.shields.io/badge/node.js-%3E=16.x-green.svg" alt="Node.js Required">
  <img src="https://img.shields.io/badge/individual%20use-free-brightgreen.svg" alt="Free for Individuals">
  <img src="https://img.shields.io/badge/commercial%20use-contact%20admin%40ambientflare.com-red.svg" alt="Commercial License Required">
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
- [Adding Your First Project](#adding-your-first-project)
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

- **Python 3.8+** (required for the backend and core services)
- **Ollama** (for embeddings, must be installed locally): [https://ollama.com/](https://ollama.com/)
- **Node.js** (required for the MCP server and frontend builds): [https://nodejs.org/](https://nodejs.org/)
- **Git** (for cloning the repository)
- **Supervisor** (process manager, usually installed by the setup scripts)
- **(Optional) npm/yarn** (if you plan to modify/rebuild the frontend)

**Platform-specific:**
- **Windows:** Run the installer as Administrator.
- **Linux/Mac:** Must have `bash`, `sudo`, and permission to `chmod +x` scripts.

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

## Adding Your First Project

Augmentorium is designed to monitor and index one or more project folders. When you add a project, the server will automatically watch that folder for changes and update the RAG (Retrieval-Augmented Generation) index in real time. This ensures your codebase and knowledge graph are always up to date.

### Ways to Add a Project

**1. Using the Built-in Web UI:**
- Open the Augmentorium web interface in your browser (usually at [http://localhost:6656](http://localhost:6656)).
- Use the "Add Project" feature and provide a name and the path to your project folder.
- The server will begin monitoring the folder immediately.

**2. Using an LLM/Agent Command:**
- You can instruct your connected LLM/agent (such as Cline, Roo, Claude Coder, Windsurf, etc.) to add a project by providing the project name and path.
- Example prompt: `Add a project named "MyApp" at path "C:/Users/you/code/MyApp"`

**Project Monitoring:**
- Once a project is added, any changes (file additions, deletions, edits) in the folder will be detected and the RAG index will be updated automatically.
- You can add multiple projects; each will be tracked independently.

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

This project is licensed under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/).

- **Free for personal, non-commercial use by individuals.**
- **Commercial use by organizations, companies, or for-profit entities is NOT permitted under this license.**
- To obtain a commercial license, please contact: admin@ambientflare.com

By using this software, you agree to these terms.

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
