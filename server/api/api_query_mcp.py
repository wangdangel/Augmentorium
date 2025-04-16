from flask import Blueprint, jsonify, request, current_app, g
from server.api.project_helpers import get_project_path

query_mcp_bp = Blueprint('query_mcp', __name__, url_prefix='/api/query/mcp')

@query_mcp_bp.route('/', methods=['POST'])
def process_query_mcp():
    """
    MCP/LLM-friendly query endpoint. Requires a project name and a query string.
    POST body: { "project": "...", "query": "...", ... }
    Returns: { "results": [...], "context": ... }
    """
    data = request.get_json(force=True)
    project_name = data.get("project")
    query = data.get("query")
    n_results = data.get("n_results", 10)
    min_score = data.get("min_score", 0.0)
    filters = data.get("filters")

    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    if not query:
        return jsonify({"error": "Query must be specified."}), 400

    config_manager = getattr(g, "config_manager", None)
    if config_manager is None:
        config_manager = getattr(current_app, "config_manager", None)
    if config_manager is None:
        return jsonify({"error": "No config manager found"}), 500

    project_path = get_project_path(config_manager, project_name)
    if not project_path:
        return jsonify({"error": "Project not found"}), 404

    # Get the project-specific query_processor and relationship_enricher
    query_processor = getattr(current_app, "query_processor", None)
    relationship_enricher = getattr(current_app, "relationship_enricher", None)
    context_builder = getattr(current_app, "context_builder", None)

    if not query_processor or not relationship_enricher or not context_builder:
        return jsonify({"error": "Server internal error: QueryProcessor, RelationshipEnricher, or ContextBuilder not initialized"}), 500

    # Run the query (do NOT pass project as kwarg, assume processor is project-scoped)
    try:
        results = query_processor.query(
            query_text=query,
            n_results=n_results,
            min_score=min_score,
            filters=filters
        )
        # Optionally enrich results with relationships
        results = relationship_enricher.enrich_results(results)
        # Optionally build context
        context = context_builder.build_context(query, results)
        return jsonify({
            "context": context,
            "results": [r.to_dict() for r in results]
        })
    except Exception as e:
        return jsonify({"error": f"Query failed: {str(e)}"}), 500
