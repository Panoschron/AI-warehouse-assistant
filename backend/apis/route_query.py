from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from backend import app_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class Constraint(BaseModel):
    field: str
    value: str


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    constraints: Optional[List[Constraint]] = None


class MatchItem(BaseModel):
    code: str
    description: str
    location: Optional[str] = None
    location_state: Literal["present", "empty"]
    explain: str
    score: Optional[float] = None


class Clarifying(BaseModel):
    field: str
    label: str
    options: List[str]


class QueryResponse(BaseModel):
    presentation: Literal["single", "list", "clarifying", "empty"]
    matches: List[MatchItem]
    clarifying: Optional[Clarifying] = None
    empty: bool
    nl_response: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, request: Request) -> QueryResponse:
    pipeline = getattr(request.app.state, "pipeline", None)

    try:
        if pipeline is None:
            logger.error("Query pipeline not initialized")
            raise HTTPException(status_code=503, detail="Query pipeline not initialized")

        if not (payload.query or "").strip():
            raise HTTPException(status_code=400, detail="query must be a non-empty string")

        effective_top_k = payload.top_k if payload.top_k is not None else app_settings.DEFAULT_TOP_K

        if effective_top_k <= 0:
            raise HTTPException(status_code=400, detail="top_k must be a positive integer")

        response = pipeline.search_with_llm(
            query=payload.query,
            top_k=effective_top_k,
            constraints=[c.model_dump() for c in (payload.constraints or [])],
        )
        return QueryResponse(
            presentation=response.get("presentation") or ("empty" if response.get("empty") else "list"),
            matches=response.get("matches") or [],
            clarifying=response.get("clarifying"),
            empty=bool(response.get("empty")),
            nl_response=response.get("nl_response"),
        )

    except HTTPException as he:
        logger.exception(f"HTTP error during query processing: {he.status_code} - {he.detail}")
        raise he

    except Exception:
        logger.exception("Unhandled error in query_endpoint")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Warehouse Assistant"}
