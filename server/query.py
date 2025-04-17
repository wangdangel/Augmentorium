"""
Query processor for Augmentorium
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from functools import lru_cache

from utils.db_utils import VectorDB
from indexer.embedder import OllamaEmbedder
from utils.text_preprocessing import preprocess_text
from utils.synonyms import SYNONYM_DICT
from utils.graph_db import get_connection, get_nodes_by_file_path, get_edges_for_node, get_node_by_id
logger = logging.getLogger(__name__)

class QueryExpander:
    """Query expander for improving retrieval"""
    
    def __init__(self, ollama_embedder: OllamaEmbedder):
        """
        Initialize query expander

        Args:
            ollama_embedder: Ollama embedder (required)
        """
        self.ollama_embedder = ollama_embedder
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand a query with related terms (cartesian product synonym expansion).

        Args:
            query: Original query

        Returns:
            List[str]: List of expanded queries (original + all synonym combinations)
        """
        from itertools import product
        import re

        # Use imported synonym dictionary
        synonym_dict = SYNONYM_DICT

        # Tokenize query (simple whitespace split)
        tokens = query.split()
        # For each token, get [token] or [synonyms...]
        synonym_options = []
        for token in tokens:
            key = token.lower()
            if key in synonym_dict:
                options = [token] + [syn for syn in synonym_dict[key]]
            else:
                options = [token]
            synonym_options.append(options)

        # Cartesian product to generate all combinations
        expanded_queries = set()
        for combination in product(*synonym_options):
            expanded = " ".join(combination)
            # Normalize: lowercase, strip, collapse whitespace
            normalized = re.sub(r"\s+", " ", expanded.strip().lower())
            expanded_queries.add(normalized)

        return list(expanded_queries)
        import re
        from itertools import product

        # Tokenize query (simple whitespace split)
        tokens = query.split()
        # For each token, get [token] or [synonyms...]
        synonym_options = []
        for token in tokens:
            key = token.lower()
            if key in synonym_dict:
                # preserve original casing
                options = [token] + [syn for syn in synonym_dict[key]]
            else:
                options = [token]
            synonym_options.append(options)

        # Cartesian product to generate all combinations
        expanded_queries = set()
        for combination in product(*synonym_options):
            expanded = " ".join(combination)
            # Normalize: lowercase, strip, collapse whitespace
            normalized = re.sub(r"\s+", " ", expanded.strip().lower())
            expanded_queries.add(normalized)

        return list(expanded_queries)
    
    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Get embedding for a query
        
        Args:
            query: Query to embed
            
        Returns:
            Optional[List[float]]: Embedding vector, or None if failed
        """
        return self.ollama_embedder.get_embedding(query)


class QueryResult:
    """Result of a query"""
    
    def __init__(
        self,
        chunk_id: str,
        text: str,
        metadata: Dict[str, Any],
        score: float,
        file_path: str
    ):
        """
        Initialize query result
        
        Args:
            chunk_id: ID of the code chunk
            text: Text content of the chunk
            metadata: Metadata for the chunk
            score: Relevance score
            file_path: Path to the file
        """
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata
        self.score = score
        self.file_path = file_path
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
            "score": self.score,
            "file_path": self.file_path
        }


class QueryProcessor:
    """Processor for queries"""
    def __init__(
        self,
        vector_db: VectorDB,
        expander: QueryExpander,
        collection_name: str = "code_chunks",
        cache_size: int = 100,
        remove_stopwords_for_queries: bool = False,
        graph_db_path: Optional[str] = None
    ):
        """
        Initialize query processor

        Args:
            vector_db: Vector database
            expander: Query expander (required)
            collection_name: Name of the collection
            cache_size: Size of the LRU cache
            graph_db_path: Path to the graph database (for hybrid enrichment)
        """
        self.vector_db = vector_db
        self.expander = expander
        self.collection_name = collection_name
        self.cache_size = cache_size
        self.remove_stopwords_for_queries = remove_stopwords_for_queries
        self.graph_db_path = graph_db_path
        self.relationship_enricher = RelationshipEnricher(
            vector_db, collection_name, graph_db_path=graph_db_path
        )
    
    @lru_cache(maxsize=100)
    def query(
        self,
        query_text: str,
        n_results: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[QueryResult]:
        """
        Query the vector database
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            min_score: Minimum relevance score
            filters: Filters for metadata
            
        Returns:
            List[QueryResult]: List of query results
        """
        try:
            logger.info(f"Processing query: {query_text}")
            
            # Preprocess query text (identical to document preprocessing, with optional stopword removal)
            preprocessed_query = preprocess_text(
                query_text,
                remove_stopwords_flag=self.remove_stopwords_for_queries
            )

            # Expand query (using preprocessed query)
            expanded_queries = self.expander.expand_query(preprocessed_query)

            # Get embedding for query (using preprocessed query)
            embedding = self.expander.get_query_embedding(preprocessed_query)
            if not embedding:
                logger.error("Failed to get embedding for query")
                return []
            
            # If filters contains file_name, convert to file_path filter or basename filter
            where = filters.copy() if filters else None
            if filters and "file_name" in filters:
                file_name = filters["file_name"]
                # Support both full path and basename match
                def file_path_filter(metadata):
                    fp = metadata.get("file_path", "")
                    import os
                    return fp == file_name or os.path.basename(fp) == file_name
                # Compose a new where filter for vector_db.query
                # Since vector DB may not support python callables, filter after retrieval
                where = None
            else:
                file_path_filter = None

            results = self.vector_db.query(
                collection_name=self.collection_name,
                query_embeddings=[embedding],
                n_results=n_results,
                where=where
            )
            
            # Process results
            query_results = []
            
            if not results or "ids" not in results or not results["ids"]:
                logger.warning("No results found")
                return []
            
            # Process each result
            for i, chunk_id in enumerate(results["ids"][0]):
                if i >= len(results["documents"][0]) or i >= len(results["metadatas"][0]):
                    continue
                
                text = results["documents"][0][i]
                metadata = results["metadatas"][0][i]
                file_path = metadata.get("file_path", "")
                
                # If file_name filter is active, filter here
                if filters and "file_name" in filters:
                    import os
                    if not (file_path == filters["file_name"] or os.path.basename(file_path) == filters["file_name"]):
                        continue
                
                # Calculate score (1.0 - distance)
                score = 1.0
                if "distances" in results and results["distances"]:
                    score = 1.0 - results["distances"][0][i]
                
                # Skip if score is below threshold
                if score < min_score:
                    continue
                
                # Create result
                result = QueryResult(
                    chunk_id=chunk_id,
                    text=text,
                    metadata=metadata,
                    score=score,
                    file_path=file_path
                )
                
                query_results.append(result)
            
            logger.info(f"Found {len(query_results)} results for query: {query_text}")
            
            # Hybrid enrichment: add graph relationships
            if self.relationship_enricher:
                query_results = self.relationship_enricher.enrich_results(query_results)

            return query_results
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear the query cache"""
        self.query.cache_clear()


class RelationshipEnricher:
    """Enricher for relationship data"""
    
    def __init__(self, vector_db: VectorDB, collection_name: str = "code_chunks", graph_db_path: Optional[str] = None):
        """
        Initialize relationship enricher
        
        Args:
            vector_db: Vector database
            collection_name: Name of the collection
            graph_db_path: Path to the graph database (required for graph enrichment)
        """
        self.vector_db = vector_db
        self.collection_name = collection_name
        self.graph_db_path = graph_db_path
    
    def enrich_results(self, results: List[QueryResult]) -> List[QueryResult]:
        """
        Enrich results with both vector and graph relationship data.
        """
        try:
            if not results:
                return results

            # Collect file paths
            file_paths = {result.file_path for result in results if result.file_path}

            # Get related files (vector-based, legacy)
            related_files = {}
            for file_path in file_paths:
                related = self._get_related_files(file_path)
                related_files[file_path] = related

            # Graph DB enrichment
            graph_relationships = {}
            if self.graph_db_path:
                conn = get_connection(self.graph_db_path)
                for file_path in file_paths:
                    nodes = get_nodes_by_file_path(conn, file_path)
                    file_graph = []
                    for node in nodes:
                        node_id = node["id"]
                        # print(f"DEBUG: About to call get_edges_for_node for node_id={node_id}")
                        edges = get_edges_for_node(conn, node_id)
                        # print(f"DEBUG: Edges fetched for node_id '{node_id}': {edges}")
                        edge_info = []
                        for edge in edges:
                            target_node = get_node_by_id(conn, edge["target_id"])
                            edge_info.append({
                                "relation_type": edge["relation_type"],
                                "target_id": edge["target_id"],
                                "target_node": target_node
                            })
                        file_graph.append({
                            "node": node,
                            "edges": edge_info
                        })
                    graph_relationships[file_path] = file_graph
                conn.close()

            # Enrich metadata with both relationship types
            for result in results:
                if result.file_path in related_files:
                    result.metadata["related_files"] = related_files[result.file_path]
                if self.graph_db_path and result.file_path in graph_relationships:
                    result.metadata["graph_relationships"] = graph_relationships[result.file_path]

            return results
        except Exception as e:
            logger.error(f"Failed to enrich results: {e}")
            return results
    
    def _get_related_files(self, file_path: str) -> List[str]:
        """
        Get files related to a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            List[str]: List of related file paths
        """
        try:
            # First, get chunks for this file
            chunks = self.vector_db.get_documents(
                collection_name=self.collection_name,
                where={"file_path": file_path},
                include=["metadatas"]
            )
            
            if not chunks or not chunks.get("metadatas"):
                return []
            
            # Extract references
            references = set()
            for metadata in chunks["metadatas"]:
                # Extract imports
                if "imports" in metadata:
                    references.update(metadata["imports"])
                
                # Extract references
                if "references" in metadata:
                    references.update(metadata["references"])
            
            # Map references to files
            related_files = set()
            for ref in references:
                # Search for chunks containing the reference
                ref_chunks = self.vector_db.get_documents(
                    collection_name=self.collection_name,
                    where_document={"$contains": ref},
                    include=["metadatas"],
                    limit=10
                )
                
                if not ref_chunks or not ref_chunks.get("metadatas"):
                    continue
                
                # Extract file paths
                for metadata in ref_chunks["metadatas"]:
                    if "file_path" in metadata and metadata["file_path"] != file_path:
                        related_files.add(metadata["file_path"])
            
            return list(related_files)
        except Exception as e:
            logger.error(f"Failed to get related files: {e}")
            return []
    
    def get_neighbors(self, node_id: str) -> List[dict]:
        """
        Given a node ID, return its graph neighbors (callers, callees, imports, etc.)
        Returns a list of dicts: {"relation_type": ..., "neighbor_id": ..., "neighbor_node": ...}
        """
        # print(f"DEBUG: get_neighbors called with node_id={node_id}")
        if not self.graph_db_path:
            logger.debug(f"No graph_db_path set in RelationshipEnricher for node_id={node_id}")
            return []
        try:
            logger.info(f"[get_neighbors] node_id received: '{node_id}' (type: {type(node_id)})")
            conn = get_connection(self.graph_db_path)
            # print(f"DEBUG: About to call get_edges_for_node for node_id={node_id}")
            edges = get_edges_for_node(conn, node_id)
            # print(f"DEBUG: Edges fetched for node_id '{node_id}': {edges}")
            logger.info(f"[get_neighbors] Edges fetched for node_id '{node_id}': {edges}")
            neighbors = []
            for edge in edges:
                neighbor_id = edge["target_id"] if edge["source_id"] == node_id else edge["source_id"]
                neighbor_node = get_node_by_id(conn, neighbor_id)
                neighbors.append({
                    "relation_type": edge["relation_type"],
                    "neighbor_id": neighbor_id,
                    "neighbor_node": neighbor_node
                })
            logger.info(f"[get_neighbors] Neighbors assembled for node_id '{node_id}': {neighbors}")
            conn.close()
            return neighbors
        except Exception as e:
            # print(f"EXCEPTION in get_neighbors for node_id={node_id}: {e}")
            logger.error(f"Failed to get neighbors for node {node_id}: {e}")
            return []


class ContextBuilder:
    """Builder for LLM context"""
    
    def __init__(self, max_context_size: int = 8192):
        """
        Initialize context builder
        
        Args:
            max_context_size: Maximum size of the context
        """
        self.max_context_size = max_context_size
    
    def build_context(
        self,
        query: str,
        results: List[QueryResult],
        include_metadata: bool = True
    ) -> str:
        """
        Build context for LLM
        
        Args:
            query: Original query
            results: List of query results
            include_metadata: Whether to include metadata
            
        Returns:
            str: Context for LLM
        """
        try:
            # Start with the query
            context = f"Query: {query}\n\n"
            
            # Add code chunks
            context += "Relevant code:\n\n"
            
            for i, result in enumerate(results):
                # Check if we're exceeding the max context size
                if len(context) + len(result.text) + 100 > self.max_context_size:
                    context += f"\n... (truncated {len(results) - i} more results)"
                    break
                
                # Add separator
                context += f"--- {result.file_path} ---\n"
                
                # Add the code chunk
                context += result.text + "\n\n"
                
                # Add metadata if requested
                if include_metadata:
                    metadata_str = "Metadata:\n"
                    
                    # Add key metadata fields
                    if "name" in result.metadata:
                        metadata_str += f"- Name: {result.metadata['name']}\n"
                    
                    if "chunk_type" in result.metadata:
                        metadata_str += f"- Type: {result.metadata['chunk_type']}\n"
                    
                    if "docstring" in result.metadata and result.metadata["docstring"]:
                        metadata_str += f"- Docstring: {result.metadata['docstring']}\n"
                    
                    if "imports" in result.metadata and result.metadata["imports"]:
                        imports_str = ", ".join(result.metadata["imports"])
                        metadata_str += f"- Imports: {imports_str}\n"
                    
                    if "related_files" in result.metadata and result.metadata["related_files"]:
                        related_str = ", ".join(result.metadata["related_files"])
                        metadata_str += f"- Related files: {related_str}\n"
                    
                    # Add the metadata
                    context += metadata_str + "\n"
            
            return context
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            return f"Error building context: {e}"
