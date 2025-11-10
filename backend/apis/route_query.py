from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.scripts.query_engine_handler import QueryHandler

router = APIRouter()
#NOTE: APIRouter is used to create modular route handlers that can be included in the main FastAPI application.


class QueryRequest(BaseModel):
    query: str  
    top_k: int 

#NOTE: Basemodel is an object that automatically validates the input data and generates JSON schema for the request and response bodies.

class QueryResponse(BaseModel):
    natural_language_response: str

@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, request: Request) -> QueryResponse:
    handler: Optional[QueryHandler] = getattr(request.app.state, "handler", None)
    #NOTE: getattr is a function that retrieves an attribute from an object, if the constructor fails or didnt run on time it returns the default value (None here).
    # In this case, it retrieves the "handler" attribute from the app's state, which is expected to be an instance of QueryHandler initialized during the app's startup event.
    # If the handler is not initialized (i.e., None), it raises a 503 HTTPException indicating that the service is unavailable.
    
    if handler is None:
        raise HTTPException(status_code=503, detail="Query handler not initialized")

    try:
        natural_language_response = handler.handle_query(payload.query, top_k=payload.top_k)
        return QueryResponse(natural_language_response=natural_language_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
