from backend import app_settings 
from backend.core import query_engine
from typing import List, Dict
from pathlib import Path

class QueryHandler:

    def __init__(self, model, index_faiss, meta_entries: List[Dict]):
        self.model = model
        self.index_faiss = index_faiss
        self.meta_entries = meta_entries

    def handle_query(self, query: str, top_k: int = 5) -> List[Dict]:
        """Execute the full retrieval pipeline and return results.

        Args:
            query: Raw user query text.
            top_k: Number of nearest neighbors to retrieve from the FAISS index.

        Returns:
            A list of result dictionaries with index, distance, and metadata.
        """
        normalized_query = query_engine.process_query(query)
        query_vector = query_engine.vectorize_query(self.model, normalized_query)
        distances, indices = query_engine.search_index(self.index_faiss, query_vector, top_k=top_k)
        results = query_engine.get_results_from_entries(distances, indices, self.meta_entries)
        prompt = query_engine.prompt_to_llm(results, query)
        natural_language_response = query_engine.query_llm(prompt)

        return natural_language_response