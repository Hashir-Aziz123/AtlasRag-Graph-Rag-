from fastapi import APIRouter, HTTPException

from src.models.api_schemas import QueryRequest, QueryResponse
from src.services.router import route_user_query
from src.services.fetcher import fetch_context
from src.services.synthesizer import generate_response
from src.services.cache_manager import get_cached_response, set_cached_response

router = APIRouter()

@router.post("/", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    try:
        cached_answer = await get_cached_response(request.query)
        if cached_answer:
            return QueryResponse(
                answer=cached_answer,
                routed_intent="semantic_cache_hit"
            )
            

        parsed_query = await route_user_query(request.query)
        raw_context = await fetch_context(parsed_query, request.query)
        
        if raw_context == "No relevant information found in the databases.":
            return QueryResponse(
                answer="No data found in the current ingestion slice.",
                routed_intent=parsed_query.intent.value
            )
            
        final_answer = await generate_response(request.query, raw_context)
        
        await set_cached_response(request.query, final_answer)
        
        return QueryResponse(
            answer=final_answer,
            routed_intent=parsed_query.intent.value
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval pipeline failed: {str(e)}")