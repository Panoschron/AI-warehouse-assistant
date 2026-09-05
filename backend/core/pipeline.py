"""Query processing pipeline orchestration."""
from typing import Dict, List, Optional
import logging

from backend.clients.base_llm_client import BaseLLMClient
from backend.core.generation.explain import attach_explains, template_nl_response
from backend.core.generation.prompt_builder import PromptBuilder
from backend.core.retrieval.match_builder import build_matches
from backend.core.retrieval.query_processor import QueryProcessor
from backend.core.retrieval.result_formatter import ResultFormatter
from backend.core.retrieval.vector_search import VectorSearchEngine

logger = logging.getLogger(__name__)


class QueryPipeline:
    """Orchestrates the complete query pipeline."""

    def __init__(
        self,
        query_processor: QueryProcessor,
        search_engine: VectorSearchEngine,
        result_formatter: ResultFormatter,
        prompt_builder: Optional[PromptBuilder] = None,
        llm_client: Optional[BaseLLMClient] = None,
    ):
        self.query_processor = query_processor
        self.search_engine = search_engine
        self.result_formatter = result_formatter
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client

    def search(self, query: str, top_k: int) -> List[Dict]:
        """Execute search and return structured results."""
        logger.info(f"Processing search query: {query}")

        processed_query = self.query_processor.process(query)

        query_vector = self.search_engine.embed_query(processed_query)
        distances, indices = self.search_engine.search(query_vector, top_k=top_k)

        results = self.result_formatter.format_results(distances, indices)

        logger.info(f"Found {len(results)} results")
        return results

    def search_with_llm(
        self,
        query: str,
        top_k: int,
    ) -> Dict:
        """Retrieve matches, attach grounded explains, optionally add nl_response."""
        logger.info(f"Processing query: {query}")

        results = self.search(query, top_k=top_k)
        matches = attach_explains(
            query=query,
            matches=build_matches(results),
            prompt_builder=self.prompt_builder,
            llm_client=self.llm_client,
        )

        if not matches:
            return {
                "matches": [],
                "empty": True,
                "nl_response": template_nl_response([]),
            }

        nl_response = template_nl_response(matches)
        if self.llm_client and self.prompt_builder:
            try:
                prompt = self.prompt_builder.build_prompt(query, results)
                nl_response = self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=self.prompt_builder.system_prompt,
                )
            except Exception:
                logger.exception("NL generation failed; using template nl_response")

        return {
            "matches": matches,
            "empty": False,
            "nl_response": nl_response,
        }
