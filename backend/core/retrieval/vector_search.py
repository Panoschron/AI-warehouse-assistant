"""Vector similarity search operations."""
import logging
import numpy as np
import faiss
from typing import Tuple, List
from sentence_transformers import SentenceTransformer
from backend import app_settings

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
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[List[float], List[int]]:
        """Search FAISS index for nearest neighbors.
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return (resolved at API layer)
            
        Returns:
            Tuple of (distances, indices)
        """
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        query_vector = query_vector.astype('float32')
        
        distances, indices = self.index.search(query_vector, top_k)
        print(f"Search results distances: {distances}, indices: {indices}")
        
        logger.debug(f"Found {len(indices[0])} results")
        return distances[0].tolist(), indices[0].tolist()