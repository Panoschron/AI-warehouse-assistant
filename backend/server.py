import os
from typing import List, Dict, Optional
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import faiss

from backend import app_settings
from backend.core import query_engine
from backend.scripts.env_check import check_and_install_packages
from backend.scripts.query_engine_handler import QueryHandler
from backend.apis import route_query


app = FastAPI(title="AI Warehouse Assistant API", version="0.1.0")

# Optional: Relax CORS for local testing and simple integrations
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
    """Load heavy resources once on startup: model, FAISS index, metadata path."""

    # TODO: Install packages method improvement
    if os.getenv("WA_ENV_CHECK", "0") == "1":
        check_and_install_packages()

    model = query_engine.model
    index_path = app_settings.FAISS_INDEX_FILE
    metadata_path = app_settings.META_DATA_FILE
    if not index_path.exists():
        raise RuntimeError(f"FAISS index not found at {index_path}. Build the index first.")
    if not metadata_path.exists():
        raise RuntimeError(f"Metadata file not found at {metadata_path}. Build the index first.")
    index = faiss.read_index(str(index_path))
    meta_entries = query_engine.load_metadata(metadata_path)
    app.state.handler = QueryHandler(model=model, index_faiss=index, meta_entries=meta_entries)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}



if __name__ == "__main__":
    # For ad-hoc local runs (you can also use: uvicorn backend.server:app --reload)
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
