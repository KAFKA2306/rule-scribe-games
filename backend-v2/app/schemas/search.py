"""
Search-related Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class SearchFilters(BaseModel):
    """Filters for search requests"""
    player_count_min: Optional[int] = Field(None, ge=1, le=20)
    player_count_max: Optional[int] = Field(None, ge=1, le=20)
    play_time_min: Optional[int] = Field(None, ge=5, le=1440)  # 5 min to 24 hours
    play_time_max: Optional[int] = Field(None, ge=5, le=1440)
    complexity_min: Optional[float] = Field(None, ge=1.0, le=5.0)
    complexity_max: Optional[float] = Field(None, ge=1.0, le=5.0)
    genres: Optional[List[str]] = Field(default_factory=list)
    mechanics: Optional[List[str]] = Field(default_factory=list)
    published_after: Optional[int] = Field(None, ge=1800, le=2030)
    published_before: Optional[int] = Field(None, ge=1800, le=2030)
    
    @validator('player_count_max')
    def validate_player_count_range(cls, v, values):
        if v is not None and 'player_count_min' in values and values['player_count_min'] is not None:
            if v < values['player_count_min']:
                raise ValueError('player_count_max must be >= player_count_min')
        return v
    
    @validator('play_time_max')
    def validate_play_time_range(cls, v, values):
        if v is not None and 'play_time_min' in values and values['play_time_min'] is not None:
            if v < values['play_time_min']:
                raise ValueError('play_time_max must be >= play_time_min')
        return v


class SearchRequest(BaseModel):
    """Request model for game search"""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)
    offset: int = Field(0, ge=0)
    filters: Optional[SearchFilters] = None
    similarity_threshold: float = Field(0.7, ge=0.1, le=1.0)
    enable_fuzzy_search: bool = Field(True)
    enhance_with_ai: bool = Field(False)
    search_type: str = Field("semantic", regex="^(semantic|exact|fuzzy|hybrid)$")


class SearchResult(BaseModel):
    """Individual search result"""
    game_id: int
    title: str
    description: Optional[str] = None
    content: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    player_count: Optional[str] = None
    play_time: Optional[str] = None
    complexity: Optional[float] = None
    genres: List[str] = Field(default_factory=list)
    mechanics: List[str] = Field(default_factory=list)
    year_published: Optional[int] = None
    rating: Optional[float] = None
    ai_insight: Optional[str] = None
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Response model for search results"""
    results: List[SearchResult]
    total_results: int = Field(..., ge=0)
    query: str
    processing_time_ms: float = Field(..., ge=0)
    search_metadata: Dict[str, Any] = Field(default_factory=dict)
    suggestions: Optional[List[str]] = None
    pagination: Optional[Dict[str, Any]] = None


class SearchSuggestion(BaseModel):
    """Search suggestion model"""
    text: str
    type: str = Field(..., regex="^(game|genre|mechanic|autocomplete)$")
    popularity_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchFeedback(BaseModel):
    """Search feedback model"""
    search_id: str
    user_rating: int = Field(..., ge=1, le=5)
    helpful_results: List[int] = Field(default_factory=list)
    unhelpful_results: List[int] = Field(default_factory=list)
    feedback_text: Optional[str] = Field(None, max_length=1000)
    suggested_improvement: Optional[str] = Field(None, max_length=500)