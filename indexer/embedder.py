"""
Embedder for code chunks using Ollama API
"""

import os
import json
import time
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any, Set, Tuple, Iterator, Union
from tqdm import tqdm

from augmentorium.indexer.chunker import CodeChunk
from augmentorium.utils.db_utils import VectorDB

logger = logging.getLogger(__name__)

class OllamaEmbedder:
    """Embedder using Ollama API"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "codellama",
        batch_size: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Ollama embedder
        
        Args:
            base_url: Base URL for Ollama API
            model: Model to use for embeddings
            batch_size: Batch size for embedding requests
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries (seconds)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize embedding API endpoint
        self.embed_url = f"{self.base_url}/api/embeddings"
        
        logger.info(f"Initialized Ollama embedder with model: {self.model}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a text
        
        Args:
            text: Text to embed
            
        Returns:
            Optional[List[float]]: Embedding vector, or None if failed
        """
        try:
            # Prepare request
            data = {
                "model": self.model,
                "prompt": text
            }
            
            # Make request
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(self.embed_url, json=data)
                    response.raise_for_status()
                    
                    # Parse response
                    result = response.json()
                    embedding = result.get("embedding")
                    
                    if embedding:
                        return embedding
                    else:
                        logger.warning(f"No embedding in response: {result}")
                        time.sleep(self.retry_delay)
                except Exception as e:
                    logger.warning(f"Error getting embedding (attempt {attempt+1}): {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
            
            logger.error(f"Failed to get embedding after {self.max_retries} attempts")
            return None
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None
    
    def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Get embeddings for a batch of texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List[Optional[List[float]]]: List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        
        return embeddings


class ChunkEmbedder:
    """Embedder for code chunks"""
    
    def __init__(
        self,
        ollama_embedder: Optional[OllamaEmbedder] = None,
        batch_size: int = 10,
        max_workers: int = 4
    ):
        """
        Initialize chunk embedder
        
        Args:
            ollama_embedder: Ollama embedder
            batch_size: Batch size for embedding
            max_workers: Maximum number of worker threads
        """
        self.ollama_embedder = ollama_embedder or OllamaEmbedder()
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def embed_chunks(
        self,
        chunks: List[CodeChunk],
        show_progress: bool = True
    ) -> List[Tuple[CodeChunk, Optional[List[float]]]]:
        """
        Embed a list of code chunks
        
        Args:
            chunks: List of code chunks
            show_progress: Whether to show progress bar
            
        Returns:
            List[Tuple[CodeChunk, Optional[List[float]]]]: List of chunks with embeddings
        """
        results = []
        
        # Create batches
        batches = [chunks[i:i+self.batch_size] for i in range(0, len(chunks), self.batch_size)]
        
        # Set up progress bar
        if show_progress:
            pbar = tqdm(total=len(chunks), desc="Embedding chunks")
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for batch in batches:
                future = executor.submit(self._embed_batch, batch)
                futures.append(future)
            
            # Process results
            for future in futures:
                batch_results = future.result()
                results.extend(batch_results)
                
                if show_progress:
                    pbar.update(len(batch_results))
        
        # Close progress bar
        if show_progress:
            pbar.close()
        
        return results
    
    def _embed_batch(
        self,
        chunks: List[CodeChunk]
    ) -> List[Tuple[CodeChunk, Optional[List[float]]]]:
        """
        Embed a batch of chunks
        
        Args:
            chunks: List of code chunks
            
        Returns:
            List[Tuple[CodeChunk, Optional[List[float]]]]: List of chunks with embeddings
        """
        try:
            # Get texts to embed
            texts = [chunk.text for chunk in chunks]
            
            # Get embeddings
            embeddings = self.ollama_embedder.get_embeddings_batch(texts)
            
            # Combine chunks and embeddings
            results = []
            for chunk, embedding in zip(chunks, embeddings):
                results.append((chunk, embedding))
            
            return results
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            return [(chunk, None) for chunk in chunks]


class ChunkProcessor:
    """Processor for code chunks"""
    
    def __init__(
        self,
        vector_db: VectorDB,
        embedder: Optional[ChunkEmbedder] = None,
        collection_name: str = "code_chunks"
    ):
        """
        Initialize chunk processor
        
        Args:
            vector_db: Vector database
            embedder: Chunk embedder
            collection_name: Name of the collection
        """
        self.vector_db = vector_db
        self.embedder = embedder or ChunkEmbedder()
        self.collection_name = collection_name
    
    def process_chunks(
        self,
        chunks: List[CodeChunk],
        show_progress: bool = True
    ) -> int:
        """
        Process code chunks and store in vector database
        
        Args:
            chunks: List of code chunks
            show_progress: Whether to show progress bar
            
        Returns:
            int: Number of chunks successfully processed
        """
        try:
            # Embed chunks
            results = self.embedder.embed_chunks(chunks, show_progress)
            
            # Filter out chunks with failed embeddings
            valid_results = [(chunk, embedding) for chunk, embedding in results if embedding]
            
            if not valid_results:
                logger.warning("No valid embeddings were generated")
                return 0
            
            # Prepare data for database
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            for chunk, embedding in valid_results:
                documents.append(chunk.text)
                metadatas.append(chunk.metadata)
                ids.append(chunk.id)
                embeddings.append(embedding)
            
            # Store in vector database
            success = self.vector_db.upsert_documents(
                collection_name=self.collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            if success:
                logger.info(f"Successfully processed {len(valid_results)} chunks")
                return len(valid_results)
            else:
                logger.error("Failed to store chunks in vector database")
                return 0
        except Exception as e:
            logger.error(f"Failed to process chunks: {e}")
            return 0
    
    def remove_chunks(self, file_path: str) -> bool:
        """
        Remove chunks for a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get chunks for the file
            results = self.vector_db.get_documents(
                collection_name=self.collection_name,
                where={"file_path": file_path},
                include=["ids"]
            )
            
            if not results or not results.get("ids"):
                logger.warning(f"No chunks found for file: {file_path}")
                return True
            
            # Delete chunks
            success = self.vector_db.delete_documents(
                collection_name=self.collection_name,
                ids=results["ids"]
            )
            
            if success:
                logger.info(f"Successfully removed {len(results['ids'])} chunks for file: {file_path}")
                return True
            else:
                logger.error(f"Failed to remove chunks for file: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to remove chunks: {e}")
            return False
