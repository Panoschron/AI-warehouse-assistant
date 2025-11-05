from fastapi import APIRouter
from typing import Dict, List, Optional
from pathlib import Path
import faiss
from backend import app_settings
from backend.core import query_engine
from backend.scripts.query_engine_handler import QueryHandler
from pydantic import BaseModel, Field

router=APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., description="Το ερώτημα του χρήστη")
    top_k: int = Field(5, ge=1, le=50, description="Πλήθος αποτελεσμάτων για επιστροφή")


class QueryResponse(BaseModel):
    results: List[Dict]
    
router.post("/query", response_model=QueryResponse)
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