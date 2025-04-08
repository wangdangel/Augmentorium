"""
Database utilities for Augmentorium
"""

import os
import json
import logging
import chromadb
from typing import Dict, List, Optional, Any, Union, Tuple
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)

class VectorDB:
    """Vector database wrapper for ChromaDB"""
    
    def __init__(self, db_path: str):
        """
        Initialize the vector database
        
        Args:
            db_path: Path to the database directory
        """
        self.db_path = db_path
        
        # Ensure database directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        logger.info(f"Initialized vector database at {db_path}")
    
    def get_or_create_collection(self, name: str) -> Collection:
        """
        Get or create a collection
        
        Args:
            name: Name of the collection
            
        Returns:
            Collection: ChromaDB collection
        """
        try:
            return self.client.get_or_create_collection(name=name)
        except Exception as e:
            logger.error(f"Failed to get or create collection {name}: {e}")
            raise
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Add documents to a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of document metadata
            ids: List of document IDs
            embeddings: Optional list of pre-computed embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Add documents with or without embeddings
            if embeddings:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to collection {collection_name}: {e}")
            return False
    
    def update_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Update documents in a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of document metadata
            ids: List of document IDs
            embeddings: Optional list of pre-computed embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Update documents with or without embeddings
            if embeddings:
                collection.update(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                collection.update(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to update documents in collection {collection_name}: {e}")
            return False
    
    def upsert_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Upsert documents in a collection (add if not exists, update if exists)
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of document metadata
            ids: List of document IDs
            embeddings: Optional list of pre-computed embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Upsert documents with or without embeddings
            if embeddings:
                collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to upsert documents in collection {collection_name}: {e}")
            return False
    
    def delete_documents(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete documents from a collection
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents from collection {collection_name}: {e}")
            return False
    
    def query(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query a collection
        
        Args:
            collection_name: Name of the collection
            query_texts: Optional list of query texts
            query_embeddings: Optional list of query embeddings
            n_results: Number of results to return
            where: Optional filter on metadata
            where_document: Optional filter on document content
            include: Optional list of what to include in the results
            
        Returns:
            Dict: Query results
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Ensure at least one of query_texts or query_embeddings is provided
            if query_texts is None and query_embeddings is None:
                raise ValueError("Either query_texts or query_embeddings must be provided")
            
            # Set default include if not provided
            if include is None:
                include = ["documents", "metadatas", "distances"]
            
            # Query the collection
            if query_embeddings:
                results = collection.query(
                    query_embeddings=query_embeddings,
                    n_results=n_results,
                    where=where,
                    where_document=where_document,
                    include=include
                )
            else:
                results = collection.query(
                    query_texts=query_texts,
                    n_results=n_results,
                    where=where,
                    where_document=where_document,
                    include=include
                )
            
            return results
        except Exception as e:
            logger.error(f"Failed to query collection {collection_name}: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict: Collection statistics
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            return {
                "name": collection_name,
                "count": collection.count()
            }
        except Exception as e:
            logger.error(f"Failed to get stats for collection {collection_name}: {e}")
            return {"name": collection_name, "count": 0, "error": str(e)}
    
    def list_collections(self) -> List[str]:
        """
        List all collections in the database
        
        Returns:
            List[str]: List of collection names
        """
        try:
            return [c.name for c in self.client.list_collections()]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            bool: True if the collection exists, False otherwise
        """
        try:
            return collection_name in self.list_collections()
        except Exception:
            return False
    
    def get_document(self, collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID
        
        Args:
            collection_name: Name of the collection
            doc_id: Document ID
            
        Returns:
            Optional[Dict]: Document data, or None if not found
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            result = collection.get(ids=[doc_id], include=["documents", "metadatas", "embeddings"])
            
            if not result["ids"]:
                return None
            
            return {
                "id": result["ids"][0],
                "document": result["documents"][0] if "documents" in result else None,
                "metadata": result["metadatas"][0] if "metadatas" in result else None,
                "embedding": result["embeddings"][0] if "embeddings" in result else None
            }
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from collection {collection_name}: {e}")
            return None
    
    def get_documents(
        self,
        collection_name: str,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get documents from a collection with optional filtering
        
        Args:
            collection_name: Name of the collection
            where: Optional filter on metadata
            limit: Optional limit on number of results
            offset: Optional offset for pagination
            include: Optional list of what to include in the results
            
        Returns:
            Dict: Documents data
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Set default include if not provided
            if include is None:
                include = ["documents", "metadatas"]
            
            # Get documents
            return collection.get(
                where=where,
                limit=limit,
                offset=offset,
                include=include
            )
        except Exception as e:
            logger.error(f"Failed to get documents from collection {collection_name}: {e}")
            return {"ids": [], "documents": [], "metadatas": []}
