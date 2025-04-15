from flask import Blueprint, jsonify, request, current_app
from server.api.common import require_active_project

query_bp = Blueprint('query', __name__, url_prefix='/api/query')

@query_bp.route('/', methods=['POST'])
@require_active_project
def process_query():
    """
    Process a query.
    Requires: config_manager, query_processor, relationship_enricher, context_builder on current_app.
    """
    config_manager = getattr(current_app, "config_manager", None)
    query_processor = getattr(current_app, "query_processor", None)
    relationship_enricher = getattr(current_app, "relationship_enricher", None)
    context_builder = getattr(current_app, "context_builder", None)
    # Debug logging for query_processor
    import logging
    logging.info(f"[DEBUG] query_processor: {query_processor} (type: {type(query_processor)})")
    if not query_processor or not relationship_enricher or not context_builder:
        return jsonify({"error": "Server internal error: Query components not initialized"}), 500
    
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Missing query"}), 400

    query = data["query"]
    n_results = data.get("n_results", 10)
    min_score = data.get("min_score", 0.0)
    filters = data.get("filters")
    include_metadata = data.get("include_metadata", True)

    # Thread safety for project reloads and queries is assumed to be handled at a higher level if needed
    # Debug log before calling .query
    logging.info(f"[DEBUG] About to call query_processor.query() with query_processor: {query_processor}")
    results = query_processor.query(
        query_text=query,
        n_results=n_results,
        min_score=min_score,
        filters=filters
    )

    results = relationship_enricher.enrich_results(results)

    context = context_builder.build_context(
        query=query,
        results=results,
        include_metadata=include_metadata
    )

    return jsonify({
        "context": context,
        "results": [result.to_dict() for result in results]
    })

@query_bp.route('/cache', methods=['DELETE'])
@require_active_project
def clear_cache():
    """
    Clear query cache.
    Requires: config_manager, query_processor on current_app.
    """
    query_processor = getattr(current_app, "query_processor", None)
    if not query_processor:
        return jsonify({"error": "Server internal error: QueryProcessor not initialized"}), 500
    
    query_processor.clear_cache()
    return jsonify({"status": "success", "message": "Query cache cleared"})