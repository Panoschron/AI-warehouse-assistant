from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.scripts.query_engine_handler import QueryHandler

router = APIRouter()

class QueryRequest(BaseModel):
    query: str  
    top_k: int 

class QueryResponse(BaseModel):
    results: List[Dict]

@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, request: Request) -> QueryResponse:
    handler: Optional[QueryHandler] = getattr(request.app.state, "handler", None)
    if handler is None:
        raise HTTPException(status_code=503, detail="Query handler not initialized")

    try:
        results = handler.handle_query(payload.query, top_k=payload.top_k)
        return QueryResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))