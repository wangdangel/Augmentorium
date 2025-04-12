"""
Embedder for code chunks using Ollama API
"""

import os
import json
import time
import logging
import requests
import sys
import yaml
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any, Set, Tuple, Iterator, Union
from tqdm import tqdm
from utils.text_preprocessing import preprocess_text

from indexer.chunker import CodeChunk
from utils.db_utils import VectorDB
from utils.graph_db import get_connection, insert_or_update_node, insert_edge

logger = logging.getLogger(__name__)

def load_ollama_config(config_path: str = os.path.join(os.path.dirname(__file__), "..", "config.yaml")) -> dict:
    """
    Load Ollama configuration from YAML file.
    Returns dict with keys: base_url, embedding_model, embedding_batch_size
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        ollama_cfg = config.get("ollama", {})
        return {
            "base_url": ollama_cfg.get("base_url", "http://localhost:11434"),
            "embedding_model": ollama_cfg.get("embedding_model", "bge-m3:latest"),
            "embedding_batch_size": ollama_cfg.get("embedding_batch_size", 10)
        }
    except Exception as e:
        logger.warning(f"Failed to load Ollama config from {config_path}: {e}")
        # Fallback defaults
        return {
            "base_url": "http://localhost:11434",
            "embedding_model": "bge-m3:latest",
            "embedding_batch_size": 10
        }

# Removed top-level config loading to prevent unwanted initialization/logging at import time.

class OllamaEmbedder:
    """Embedder using Ollama API"""
    
    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        batch_size: int = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        warmup_timeout: float = 120.0,
        warmup_interval: float = 2.0
    ):
        """
        Initialize Ollama embedder

        Args:
            base_url: Base URL for Ollama API
            model: Model to use for embeddings
            batch_size: Batch size for embedding requests
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries (seconds)
            warmup_timeout: Max seconds to wait for model to load
            warmup_interval: Seconds between warmup checks
        """
        if base_url is None or model is None or batch_size is None:
            config = load_ollama_config()
            base_url = base_url or config["base_url"]
            model = model or config["embedding_model"]
            batch_size = batch_size or config["embedding_batch_size"]

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.warmup_timeout = warmup_timeout
        self.warmup_interval = warmup_interval
        self.disabled = False

        # Initialize embedding API endpoint
        self.embed_url = f"{self.base_url}/api/embeddings"

        logger.info(f"Initialized Ollama embedder with model: {self.model}")
        self._verify_ollama()

    def warm_up(self):
        """
        Wait until Ollama model is loaded and responsive.
        """
        logger.info(f"Starting Ollama warm-up for model '{self.model}' (timeout {self.warmup_timeout}s)...")
        start_time = time.time()
        while True:
            try:
                tags_url = f"{self.base_url}/api/tags"
                response = requests.get(tags_url, timeout=5)
                response.raise_for_status()
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                if self.model in models:
                    logger.info(f"Ollama model '{self.model}' is loaded and ready.")
                    return True
                else:
                    logger.info(f"Ollama model '{self.model}' not yet loaded, waiting...")
            except Exception as e:
                logger.info(f"Ollama warm-up check failed: {e}, retrying...")
            if time.time() - start_time > self.warmup_timeout:
                logger.warning(f"Ollama warm-up timed out after {self.warmup_timeout}s.")
                return False
            time.sleep(self.warmup_interval)
    
    def _verify_ollama(self):
        """
        Verify Ollama server is reachable and model is available or will be downloaded.
        """
        try:
            tags_url = f"{self.base_url}/api/tags"
            response = requests.get(tags_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            if self.model in models:
                logger.info(f"Ollama server reachable. Model '{self.model}' is installed.")
            else:
                logger.info(f"Ollama server reachable. Model '{self.model}' is NOT installed. It will be downloaded on first use.")
        except Exception as e:
            logger.error(f"Could not verify Ollama server or model '{self.model}': {e}")
            logger.error("Ollama server unreachable. Exiting indexer to avoid indexing without embeddings.")
            print("ERROR: Ollama server unreachable. Please start Ollama or check your configuration.")
            sys.exit(1)

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a text
        
        Args:
            text: Text to embed
            
        Returns:
            Optional[List[float]]: Embedding vector, or None if failed
        """
        if self.disabled:
            logger.warning("Ollama embedder disabled. Returning None for embedding.")
            return None
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
        if self.disabled:
            logger.warning("Ollama embedder disabled. Returning None for all embeddings.")
            return [None for _ in texts]
        
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
        max_workers: int = 1
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
            # Preprocess each chunk's text before embedding
            texts = [preprocess_text(chunk.text) for chunk in chunks]
            
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
                # Sanitize metadata: convert lists to strings, remove empty lists
                sanitized_meta = {}
                for k, v in chunk.metadata.items():
                    if isinstance(v, list):
                        sanitized_meta[k] = ", ".join(str(item) for item in v)
                    elif v is None:
                        sanitized_meta[k] = ""
                    else:
                        sanitized_meta[k] = v
                metadatas.append(sanitized_meta)
                ids.append(chunk.id)
                embeddings.append(embedding)
            
            # Deduplicate IDs and corresponding data
            seen_ids = set()
            deduped_ids = []
            deduped_documents = []
            deduped_metadatas = []
            deduped_embeddings = []
            for id_val, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
                if id_val not in seen_ids:
                    seen_ids.add(id_val)
                    deduped_ids.append(id_val)
                    deduped_documents.append(doc)
                    deduped_metadatas.append(meta)
                    deduped_embeddings.append(emb)

            # Store in vector database
            success = self.vector_db.upsert_documents(
                collection_name=self.collection_name,
                documents=deduped_documents,
                metadatas=deduped_metadatas,
                ids=deduped_ids,
                embeddings=deduped_embeddings
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
                where={"file_path": file_path}
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
