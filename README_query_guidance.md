# Query Guidance for Augmentorium Vector Search

To get the best results from the Augmentorium code/documentation search system, use the following tips when formulating queries. This guidance applies to both human users and LLMs.

## What Types of Queries Work Best?

The system is optimized to retrieve code and documentation chunks such as:
- **Function names** (e.g., `process_documents`, `get_user_by_id`)
- **Class names** (e.g., `DocumentIndexer`, `GraphDB`)
- **Code snippets** (e.g., `def preprocess_text(text):`)
- **Docstrings or documentation comments** (e.g., `"Returns a list of matching documents."`)
- **Natural language descriptions** of code functionality (e.g., "How do I upload a document?" or "Find all functions that process user input")

## Tips for Effective Queries

- **Be specific:** Use exact function or class names if you know them.
- **Paste code snippets:** Searching with a line or block of code will often return the most relevant chunk.
- **Use docstring text:** If you remember a phrase from a docstring or comment, use it in your query.
- **Describe the functionality:** If you don't know the exact name, describe what the code does in plain English.
- **Combine keywords:** You can combine function names, class names, and descriptive terms for more targeted results.

## Advanced Options

- **Adjust result count:** Use the "Results" option to control how many matches are returned.
- **Set minimum score:** Increase the "Min Score" to filter out less relevant results.
- **Include metadata:** Enable "Include Metadata" to see file paths, function/class names, and docstrings in the results.

## For LLMs

- Prefer queries that match the structure of indexed chunks (function/class names, code blocks, or docstrings).
- When rewriting or expanding queries, align the style with how code and documentation are written in the codebase.
- Use synonyms or related terms if the initial query does not return relevant results.

---

By following these guidelines, both users and LLMs can maximize the relevance and quality of search results in Augmentorium.