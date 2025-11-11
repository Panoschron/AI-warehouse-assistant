from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    natural_language: bool = True  # Default to NL response


class SearchResult(BaseModel):
    index: int
    similarity: float
    metadata: Dict


class QueryResponse(BaseModel):
    natural_language_response: Optional[str] = None
    output_text: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, request: Request) -> QueryResponse:
    """Query the warehouse with optional natural language response."""
    
    pipeline = getattr(request.app.state, "pipeline", None)
    
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Query pipeline not initialized")
    
    try:
        if payload.natural_language:
            # Full pipeline with LLM
            response = pipeline.search_with_llm(
                query=payload.query,
                top_k=payload.top_k
            )
            return QueryResponse(**response)
        

            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Warehouse Assistant"}

