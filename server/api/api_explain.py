from flask import Blueprint, request, jsonify, g, current_app
from server.api.project_helpers import get_project_path

explain_bp = Blueprint('explain', __name__, url_prefix='/api/explain')

@explain_bp.route('/', methods=['POST'])
def explain_result():
    """
    Explain why a result was retrieved (vector score, graph path, etc.).
    Request: { "project": str (required), "query": str, "result": dict }
    Response: { "explanation": str, ... }
    """
    data = request.json or {}
    project_name = data.get("project")
    if not project_name:
        return jsonify({"error": "Project name must be specified."}), 400
    query = data.get("query")
    result = data.get("result")
    if not query or not result:
        return jsonify({"error": "Missing query or result"}), 400

    config_manager = getattr(g, "config_manager", None)
    if config_manager is None:
        config_manager = getattr(current_app, "config_manager", None)
    if config_manager is None:
        return jsonify({"error": "No config manager found"}), 500

    project_path = get_project_path(config_manager, project_name)
    if not project_path:
        return jsonify({"error": "Project not found"}), 404

    # Use the actual query_processor and relationship_enricher logic, routed by project
    query_processor = getattr(current_app, "query_processor", None)
    relationship_enricher = getattr(current_app, "relationship_enricher", None)
    if not query_processor or not relationship_enricher:
        return jsonify({"error": "Server internal error: QueryProcessor or RelationshipEnricher not initialized"}), 500

    # If your processors are project-specific, replace with a lookup by project_name
    explanation = query_processor.explain(
        query=query,
        result=result,
        project=project_name
    )

    # Optionally, enrich with graph info
    graph_explanation = relationship_enricher.explain(
        query=query,
        result=result,
        project=project_name
    )

    return jsonify({
        "explanation": explanation,
        "graph_explanation": graph_explanation
    })
