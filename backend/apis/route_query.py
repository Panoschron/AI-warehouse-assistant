from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional
from pydantic import BaseModel
from backend import app_settings
import logging 

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


class SearchResult(BaseModel):
    index: int
    metadata: Dict


class QueryResponse(BaseModel):
    nl_response: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, request: Request) -> QueryResponse:
    pipeline = getattr(request.app.state, "pipeline", None)

    try:
        if pipeline is None:
            logger.error("Query pipeline not initialized")
            raise HTTPException(status_code=503, detail="Query pipeline not initialized")

        effective_top_k = payload.top_k if payload.top_k is not None else app_settings.DEFAULT_TOP_K

        if effective_top_k <= 0:
            raise HTTPException(status_code=400, detail="top_k must be a positive integer")

        response = pipeline.search_with_llm(
            query=payload.query,
            top_k=effective_top_k
        )
        return QueryResponse(nl_response=response)

    except HTTPException as he:
        logger.exception(f"HTTP error during query processing: {he.status_code} - {he.detail}")
        raise he

    except Exception as e:
        logger.exception("Unhandled error in query_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Warehouse Assistant"}

