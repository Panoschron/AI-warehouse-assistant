import os
from typing import List, Dict, Optional
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import faiss
from sentence_transformers import SentenceTransformer

from backend import app_settings
from backend.core import query_engine
from backend.scripts.env_check import check_and_install_packages
from backend.scripts.query_engine_handler import QueryHandler
from backend.apis import route_query


app = FastAPI(title="AI Warehouse Assistant API", version="0.1.0")

# Optional: Relax CORS for local testing and simple integrations
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"],)


app.include_router(route_query.router, prefix="", tags=["query"])

@app.on_event("startup")
def startup_event() -> None:
    """Load heavy resources once on startup."""
    #check_and_install_packages()
    
    # Load model and index
    model = SentenceTransformer(app_settings.DEFAULT_EMBEDDING_MODEL)
    index = faiss.read_index(str(app_settings.FAISS_INDEX_FILE))
    
    # Load metadata
    from backend.core.query_engine import load_metadata
    meta_entries = load_metadata(app_settings.META_DATA_FILE)
    
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
    prompt_builder = PromptBuilder(max_context_items=3)
    llm_client = OpenAIClient()
    
    # Create pipeline
    pipeline = QueryPipeline(
        query_processor=query_processor,
        search_engine=search_engine,
        result_formatter=result_formatter,
        prompt_builder=prompt_builder,
        llm_client=llm_client
    )
    
    app.state.pipeline = pipeline


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}



if __name__ == "__main__":
    # For ad-hoc local runs (you can also use: uvicorn backend.server:app --reload)
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
