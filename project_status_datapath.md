# Project Status Data Path (Mermaid Diagram)

```mermaid
flowchart TD
    subgraph Indexer
        A[Indexer process]
        B[POST /api/indexer/status]
    end

    subgraph Backend
        C[/api/indexer/status handler<br>(api_indexer.py)]
        D[indexer_status variable]
        E[/api/projects/ handler<br>(api_projects.py)]
    end

    subgraph Frontend
        F[fetchProjects() API call]
        G[ProjectsPage.tsx]
        H[ProjectList.tsx]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
```

**Explanation:**  
- The Indexer process sends status updates to the backend via POST `/api/indexer/status`.
- The backend handler stores this in a variable (`indexer_status`).
- The `/api/projects/` endpoint reads from this variable to provide project statuses.
- The frontend fetches this data and displays it on the Projects page.

If the backend does not share the same `indexer_status` object between these endpoints, the UI will not update with real-time statuses.