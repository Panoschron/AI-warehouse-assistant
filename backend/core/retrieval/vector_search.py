"""Vector similarity search operations."""
import logging
import numpy as np
import faiss
from typing import Tuple, List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorSearchEngine:
    """Handles embedding and FAISS search operations."""
    
    def __init__(self, model: SentenceTransformer, index: faiss.Index):
        self.model = model
        self.index = index
        self._dimension = index.d
    
    def embed_query(self, query: str) -> np.ndarray:
        """Convert text query to embedding vector.
        
        Args:
            query: Text to embed
            
        Returns:
            Normalized embedding vector
        """
        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        logger.debug(f"Embedded query to {embedding.shape} vector")
        return embedding
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> Tuple[List[float], List[int]]:
        """Search FAISS index for nearest neighbors.
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            
        Returns:
            Tuple of (distances, indices)
        """
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        query_vector = query_vector.astype('float32')
        
        distances, indices = self.index.search(query_vector, top_k)
        
        logger.debug(f"Found {len(indices[0])} results")
        return distances[0].tolist(), indices[0].tolist()