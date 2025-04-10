# Augmentorium Refactor & Frontend Roadmap (Updated)

---

## **Phase 1: Refactor Augmentorium API Server** ✅ *Completed*

- Removed embedded MCP server logic
- API server now initializes RAG, indexer, and database components directly
- Exposes REST endpoints for project management, query, and cache
- No authentication (local-only)
- Files kept modular and under 500 lines

---

## **Phase 2: Build Separate MCP Server** ✅ *Completed*

- Created standalone MCP server using MCP Python SDK (`FastMCP`)
- MCP server calls API server via HTTP
- Communicates with LLM via stdin/stdout
- Fully decoupled from API server

---

## **Phase 3: Frontend Development** ✅ *Completed (Scaffolded)*

- React + TypeScript + Vite project initialized
- React Router with navigation menu
- Pages scaffolded:
  - **Projects** (working: list, add, remove)
  - **Documents** (scaffolded: upload, re-index placeholders)
  - **Query** (working: search, display results)
  - **Graph** (placeholder)
  - **Settings** (working: clear cache)
  - **MCP Tools** (placeholder)
- Proxy configured to backend API
- Modular components under 500 lines

---

## **Phase 4: Feature Development & UI Enhancements** (Next)

- **Projects**
  - Set active project with persistent state
  - Project metadata editing
- **Documents**
  - Implement file upload API
  - List indexed documents dynamically
  - Trigger and monitor re-indexing
- **Query**
  - Advanced filters and options
  - Result highlighting
- **Graph**
  - Interactive visualization of code relationships
  - Filter and navigation features
- **Settings**
  - Server status display
  - Log viewing
  - Config management
- **MCP Tools**
  - List and invoke MCP server tools/resources
  - Display results
- **UX**
  - Responsive design improvements
  - Dark/light mode toggle
  - Notifications and error handling
  - Loading indicators

---

## **Future Enhancements**

- Add WebSocket/SSE support for real-time updates
- Add analytics and usage dashboards
- Extend MCP server with more tools/resources
- Add plugin system for custom extensions

---

**Note:** Continue to keep all files modular and under 500 lines by splitting into submodules and helpers as needed.
