"""Format search results."""
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ResultFormatter:
    """Formats raw search results into structured output."""
    
    def __init__(self, metadata_entries: List[Dict]):
        self.metadata_entries = metadata_entries
    
    def format_results(
        self, 
        distances: List[float], 
        indices: List[int],
        include_distance: bool = True
    ) -> List[Dict]:
        """Map search results to metadata entries.
        
        Args:
            distances: Similarity distances
            indices: Metadata indices
            include_distance: Whether to include distance in output
            
        Returns:
            List of formatted result dictionaries
        """
        results = []
        
        for dist, idx in zip(distances, indices):
            if 0 <= idx < len(self.metadata_entries):
                entry = self.metadata_entries[idx]
                
                result = {
                    "index": idx,
                    "metadata": entry
                }
                
                if include_distance:
                    result["distance"] = float(dist)
                    result["similarity"] = float(1 - dist)  # Convert distance to similarity
                
                results.append(result)
            else:
                logger.warning(f"Invalid index {idx} (max: {len(self.metadata_entries)})")
        
        return results