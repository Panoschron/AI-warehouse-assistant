from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    index: int
    metadata: Dict


class QueryResponse(BaseModel):
    nl_response: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, request: Request) -> QueryResponse:
    """Query the warehouse with optional natural language response."""
    
    pipeline = getattr(request.app.state, "pipeline", None)
    
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Query pipeline not initialized")
    
    try:

            response = pipeline.search_with_llm(
                query=payload.query,
                top_k=payload.top_k
            )
            return QueryResponse(nl_response=response)
        

            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Warehouse Assistant"}

