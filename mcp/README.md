# MCP Node.js Server for Augmentorium

This server implements the Model Context Protocol (MCP) for connecting to the Augmentorium RAG server, now fully in Node.js and communicating via **standard IO** (stdin/stdout), not SSE or REST.

## Features
- **Node.js implementation** for fast, reliable agent integration
- **Standard IO only**: designed for LLM/agent orchestration (Klein Claude, Claude, GPT, etc.)
- **No Python dependencies**
- **No manual process management**: launched and managed by the platform installer and Supervisor

## Project Structure
- `mcp-server.js` – Main entry point (STDIN/STDOUT transport)
- `dist/` – Compiled/bundled code
- `tsconfig.json` – TypeScript configuration

## Usage
**You do not need to manually launch or configure the MCP server.**

- The platform installer and Supervisor will handle everything automatically.
- For advanced agent integration, connect via standard IO.

## For Klein Claude AI Windsurf
- Set the MCP server to use standard IO (STDIN/STDOUT communication).
- No Python dependencies or manual process management required.
- For protocol details, see the [MCP documentation](https://github.com/modelcontextprotocol)

---

## Troubleshooting
- If the MCP server is not responding, rerun the platform installer to restart all services.
- For advanced debugging, check the Supervisor logs in the root directory.

---

## License
MIT
