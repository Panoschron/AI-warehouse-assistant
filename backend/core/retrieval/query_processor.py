"""Query preprocessing and normalization."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Handles query text preprocessing."""
    
    def __init__(self, lowercase: bool = True, strip: bool = True):
        self.lowercase = lowercase
        self.strip = strip
    
    def process(self, query: str) -> str:
        """Normalize and clean query text.
        
        Args:
            query: Raw user query
            
        Returns:
            Processed query string
        """
        if not query:
            raise ValueError("Query cannot be empty")
        
        processed = query
        
        if self.strip:
            processed = processed.strip()
        
        if self.lowercase:
            processed = processed.lower()
        
        logger.debug(f"Processed query: '{query}' -> '{processed}'")
        return processed