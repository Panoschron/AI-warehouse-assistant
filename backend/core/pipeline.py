"""Query processing pipeline orchestration."""
from typing import Dict, List, Optional
import logging

from backend.clients.base_llm_client import BaseLLMClient
from backend.core.generation.explain import attach_explains, template_nl_response
from backend.core.generation.prompt_builder import PromptBuilder
from backend.core.retrieval.match_builder import build_matches
from backend.core.retrieval.presentation import (
    apply_constraints,
    decide_presentation,
    normalize_constraints,
)
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

    def search(self, query: str, top_k: int) -> tuple[List[Dict], str]:
        """Execute search and return (candidate results, processed query)."""
        logger.info(f"Processing search query: {query}")

        processed_query = self.query_processor.process(query)

        ntotal = int(getattr(self.search_engine.index, "ntotal", top_k) or top_k)
        candidate_k = min(ntotal, max(top_k * 4, 12))

        query_vector = self.search_engine.embed_query(processed_query)
        distances, indices = self.search_engine.search(query_vector, top_k=candidate_k)

        results = self.result_formatter.format_results(distances, indices)

        logger.info(f"Found {len(results)} candidate results")
        return results, processed_query

    def search_with_llm(
        self,
        query: str,
        top_k: int,
        constraints: Optional[List[Dict]] = None,
    ) -> Dict:
        """Retrieve matches, apply presentation policy, optionally add nl_response."""
        logger.info(f"Processing query: {query}")

        results, processed_query = self.search(query, top_k=top_k)
        gated = apply_constraints(
            build_matches(results, query=processed_query),
            normalize_constraints(constraints),
        )
        decision = decide_presentation(query=query, matches=gated, top_k=top_k)
        matches = attach_explains(
            query=query,
            matches=decision["matches"],
            prompt_builder=self.prompt_builder,
            llm_client=self.llm_client,
        )

        presentation = decision["presentation"]
        clarifying = decision["clarifying"]
        empty = bool(decision["empty"] or not matches)

        if empty:
            return {
                "presentation": "empty",
                "matches": [],
                "clarifying": None,
                "empty": True,
                "nl_response": template_nl_response([], presentation="empty"),
            }

        nl_response = template_nl_response(
            matches,
            presentation=presentation,
            clarifying=clarifying,
        )
        if presentation != "clarifying" and self.llm_client and self.prompt_builder:
            try:
                prompt = self.prompt_builder.build_prompt(query, results)
                nl_response = self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=self.prompt_builder.system_prompt,
                )
            except Exception:
                logger.exception("NL generation failed; using template nl_response")

        return {
            "presentation": presentation,
            "matches": matches,
            "clarifying": clarifying,
            "empty": False,
            "nl_response": nl_response,
        }
