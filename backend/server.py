from typing import List, Dict, Optional
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import faiss

from backend import app_settings
from backend.core import query_engine
from backend.scripts.env_check import check_and_install_packages
from backend.scripts.query_engine_handler import QueryHandler




class QueryRequest(BaseModel):
    query: str = Field(..., description="Το ερώτημα του χρήστη")
    top_k: int = Field(5, ge=1, le=50, description="Πλήθος αποτελεσμάτων για επιστροφή")


class QueryResponse(BaseModel):
    results: List[Dict]


app = FastAPI(title="AI Warehouse Assistant API", version="0.1.0")

# Optional: Relax CORS for local testing and simple integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Load heavy resources once on startup: model, FAISS index, metadata path."""
    # Use the model already constructed in query_processor to avoid double-loading
    requirements= check_and_install_packages
    model = query_engine.model
    index_path = app_settings.FAISS_INDEX_FILE
    metadata_path = app_settings.META_DATA_FILE

    if not index_path.exists():
        raise RuntimeError(f"FAISS index not found at {index_path}. Build the index first.")
    if not metadata_path.exists():
        raise RuntimeError(f"Metadata file not found at {metadata_path}. Build the index first.")

    index = faiss.read_index(str(index_path))

    handler = QueryHandler(model=model, index_faiss=index, path_metadata=metadata_path)
    app.state.handler = handler


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest) -> QueryResponse:
    handler: Optional[QueryHandler] = getattr(app.state, "handler", None)
    if handler is None:
        raise HTTPException(status_code=503, detail="Query handler not initialized")

    try:
        results = handler.handle_query(payload.query, top_k=payload.top_k)
        return QueryResponse(results=results)
    except Exception as e:
        # Log as needed; return safe error to client
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # For ad-hoc local runs (you can also use: uvicorn backend.server:app --reload)
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
