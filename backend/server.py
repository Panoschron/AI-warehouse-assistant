import os
from typing import Dict
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import app_settings
from backend.apis import route_query
from backend.core.resource_loader import load_resources  

app = FastAPI(title="AI Warehouse Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(route_query.router, prefix="", tags=["query"])

@app.on_event("startup")
def startup_event() -> None:
    """Load resources and build the query pipeline."""
    # Load heavy resources (model, FAISS index, metadata)
    model, index, meta_entries = load_resources(
        model_name=app_settings.DEFAULT_EMBEDDING_MODEL,
        index_path=app_settings.FAISS_INDEX_FILE,
        metadata_path=app_settings.META_DATA_FILE,
    )

    # Build pipeline components
    from backend.core.retrieval.query_processor import QueryProcessor
    from backend.core.retrieval.vector_search import VectorSearchEngine
    from backend.core.retrieval.result_formatter import ResultFormatter
    from backend.core.generation.prompt_builder import PromptBuilder
    from backend.clients.openai_client import OpenAIClient
    from backend.core.pipeline import QueryPipeline

    query_processor = QueryProcessor()
    search_engine = VectorSearchEngine(model=model, index=index)
    result_formatter = ResultFormatter(metadata_entries=meta_entries)
    prompt_builder = PromptBuilder()
    llm_client = OpenAIClient()

    pipeline = QueryPipeline(
        query_processor=query_processor,
        search_engine=search_engine,
        result_formatter=result_formatter,
        prompt_builder=prompt_builder,
        llm_client=llm_client,
    )

    app.state.pipeline = pipeline

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
