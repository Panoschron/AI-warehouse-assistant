"""Query processing pipeline orchestration."""
from typing import List, Dict, Optional
import logging

from backend.core.retrieval.query_processor import QueryProcessor
from backend.core.retrieval.vector_search import VectorSearchEngine
from backend.core.retrieval.result_formatter import ResultFormatter
from backend.core.generation.prompt_builder import PromptBuilder
from backend.clients.base_llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class QueryPipeline:
    """Orchestrates the complete query pipeline."""
    
    def __init__(
        self,
        query_processor: QueryProcessor,
        search_engine: VectorSearchEngine,
        result_formatter: ResultFormatter,
        prompt_builder: Optional[PromptBuilder] = None,
        llm_client: Optional[BaseLLMClient] = None
    ):
        self.query_processor = query_processor
        self.search_engine = search_engine
        self.result_formatter = result_formatter
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Execute search and return structured results.
        
        Args:
            query: User query
            top_k: Number of results
            
        Returns:
            List of search results
        """
        logger.info(f"Processing search query: {query}")
        
        # Process query
        processed_query = self.query_processor.process(query)
        
        # Embed and search
        query_vector = self.search_engine.embed_query(processed_query)
        distances, indices = self.search_engine.search(query_vector, top_k=top_k)
        
        # Format results
        results = self.result_formatter.format_results(distances, indices)
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def search_with_llm(
        self, 
        query: str, 
        top_k: int = 5,
    ) -> Dict:
        """Execute search and generate natural language response.
        
        Args:
            query: User query
            top_k: Number of results for context
            temperature: LLM sampling temperature
            
        Returns:
            Dict with results and natural_language_response
        """
        if not self.llm_client or not self.prompt_builder:
            raise ValueError("LLM client and prompt builder required for NL generation")
        
        logger.info(f"Processing query with LLM: {query}")
        
        # Get search results
        results = self.search(query, top_k=top_k)
        
        # Build prompt and generate response
        prompt = self.prompt_builder.build_prompt(query, results)
        system_prompt = self.prompt_builder.system_prompt
        
        nl_response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        
        return nl_response