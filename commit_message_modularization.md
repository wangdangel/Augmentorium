# Commit Message: Modularize Large Indexer Files

## Summary

Refactor: Modularize large files in the indexer/ directory for improved maintainability and clarity.

## Details

- **indexer/watcher.py**: Split into file_hasher.py, file_event.py, event_handler.py, project_watcher.py, watcher_service.py. Updated all imports and references. Added a deprecation note to watcher.py.
- **indexer/chunker.py**: Split into code_chunk.py, chunking_strategy_base.py, ast_chunking_strategy.py, sliding_window_chunking_strategy.py, json_object_chunking_strategy.py, yaml_document_chunking_strategy.py, markdown_section_chunking_strategy.py, chunking_strategy_factory.py. Updated all imports and references. Added a deprecation note to chunker.py.
- **indexer/parser.py**: Split into language_grammars.py, tree_sitter_manager.py, code_structure.py, code_parser.py. Updated all imports and references. Added a deprecation note to parser.py.

## Rationale

- Improves maintainability by enforcing single-responsibility per module.
- Makes code easier to test, extend, and review.
- No logic or features were changed; only modularization and import updates were performed.

## Next Steps

- Validate all functionality and tests.
- Remove deprecated files after migration is confirmed stable.

---