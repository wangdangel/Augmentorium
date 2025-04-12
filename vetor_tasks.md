# Vector Search Alignment Process for RAG/Code Search

## Purpose

This document outlines the process and best practices for ensuring that query and document embeddings are properly aligned in a Retrieval-Augmented Generation (RAG) system for code/documentation search. The goal is to maximize retrieval quality and relevance for both LLM-driven and user-driven queries.

---

## Goals

- Ensure that queries return relevant code/documentation chunks from the vector database.
- Align embedding strategies for both queries and documents.
- Provide a living checklist for ongoing improvements.

---

## Process Checklist

### 1. Use a Code-Specific Embedding Model
- [] Select a high-quality, pretrained embedding model for code (e.g., OpenAI code models, BGE, CodeBERT, HuggingFace models).
- [x] Use the same model for both document and query embeddings.

### 2. Consistent Preprocessing
- [x] Apply identical preprocessing to both documents and queries:
  - Lowercase all text.
  - Normalize whitespace.
  - Strip markdown, comments, and docstring formatting.
  - Optionally remove stopwords (for natural language queries).

### 3. Chunking Strategy
- [x] Index documents using logical code chunks (functions, classes, docstrings) rather than arbitrary splits.
- [x] **Review and validate that tree-sitter language-aware chunking is working as intended for all supported languages and codebases.**

### 4. Query Rewriting/Expansion
- [x] Implement query rewriting or expansion (e.g., LLM-based rephrasing, synonym expansion) to match the style of indexed content.

### 5. Embedding Transformation
- [ ] Consider post-processing query embeddings (e.g., learned transformation, prompt engineering) to better align with document embeddings.

### 6. Retriever Fine-Tuning (Advanced)
- [ ] Fine-tune the retriever or re-ranker using supervised data or LLM feedback if possible.

### 7. Regular Embedding Updates
- [x] Re-embed documents when code or documentation changes.

### 8. User/LLM Guidance
- [x] Document and expose the types of queries that work best (e.g., function names, code snippets, docstrings).

### 9. Graph Database Integration
- [x] Ensure the graph database is populated with up-to-date code relationships (edges, references, etc.) during indexing.
- [x] Retrieve relevant graph data (edges, relationships) during queries to enhance LLM context and RAG results.
- [x] Review and validate that graph data is accurate and useful for code understanding and navigation.
- [x] Integrate graph data with vector search results for richer responses.

---

## System Flow

```mermaid
flowchart TD
    A[User/LLM Query] --> B[Preprocessing & Rewriting]
    B --> C[Query Embedding (Code Model)]
    C --> D[Vector Search (ChromaDB)]
    D --> E[Top-k Code/Doc Chunks]
    E --> F[RAG/LLM Generation]
    subgraph Indexing
        G[Code/Docs] --> H[Preprocessing]
        H --> I[Chunking]
        I --> J[Embedding (Same Model)]
        J --> D
        I --> K[Graph Extraction]
        K --> L[Graph DB]
    end
    F --> L
    L --> F
```

---