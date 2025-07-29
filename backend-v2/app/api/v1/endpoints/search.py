
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import structlog
from datetime import datetime

from app.core.database import get_db
from app.services.supabase_service import supabase_service
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.models.game import Game
from app.core.rate_limiter import RateLimiter

logger = structlog.get_logger()
router = APIRouter()

rate_limiter = RateLimiter()


@router.post("/", response_model=SearchResponse)
async def search_games(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Query(None)
):
    try:
        if user_id:
            await rate_limiter.check_rate_limit(user_id)
        
        start_time = datetime.utcnow()
        
        logger.info("Search request received", 
                   query=request.query, 
                   user_id=user_id,
                   filters=request.filters)
        
        search_results = await supabase_service.search_games_with_filters(
            query=request.query,
            filters=request.filters,
            limit=request.limit,
            offset=0
        )
        
        # Enhanced results (AI features can be added later)
        enhanced_results = search_results
        
        # Calculate search metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create response
        response = SearchResponse(
            results=enhanced_results,
            total_results=len(enhanced_results),
            query=request.query,
            processing_time_ms=processing_time,
            search_metadata={
                "supabase_search": True,
                "ai_enhanced": request.enhance_with_ai,
                "filters_applied": bool(request.filters)
            }
        )
        
        # Log search analytics in background
        background_tasks.add_task(
            log_search_analytics,
            user_id=user_id,
            query=request.query,
            results_count=len(enhanced_results),
            processing_time=processing_time
        )
        
        logger.info("Search completed successfully", 
                   query=request.query,
                   results_count=len(enhanced_results), 
                   processing_time=processing_time)
        
        return response
        
    except Exception as e:
        logger.error("Search failed", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search suggestions based on popular games and past searches
    """
    try:
        suggestions = await supabase_service.get_search_suggestions(
            query=query,
            limit=limit
        )
        
        return suggestions
        
    except Exception as e:
        logger.error("Failed to get suggestions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get suggestions")


@router.post("/feedback")
async def submit_search_feedback(
    search_id: str,
    feedback: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for search results to improve future searches
    """
    try:
        # Store feedback in Supabase
        await supabase_service.log_search_analytics({
            "search_id": search_id,
            "feedback": feedback,
            "event_type": "search_feedback"
        })
        
        logger.info("Search feedback received", search_id=search_id)
        
        return {"message": "Feedback received successfully"}
        
    except Exception as e:
        logger.error("Failed to store feedback", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to store feedback")


async def log_search_analytics(
    user_id: Optional[str],
    query: str,
    results_count: int,
    processing_time: float
):
    """
    Log search analytics for monitoring and improvement
    """
    try:
        # This would typically go to an analytics service
        analytics_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "query": query,
            "results_count": results_count,
            "processing_time_ms": processing_time,
            "event_type": "search"
        }
        
        logger.info("Search analytics logged", **analytics_data)
        
    except Exception as e:
        logger.error("Failed to log analytics", error=str(e))