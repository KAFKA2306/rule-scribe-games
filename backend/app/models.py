from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class GameDetail(BaseSchema):
    id: str
    slug: str
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    affiliate_urls: Optional[Dict[str, Any]] = None
    view_count: Optional[int] = 0
    search_count: Optional[int] = 0
    data_version: Optional[int] = 0
    is_official: Optional[bool] = False
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    play_time: Optional[int] = None
    min_age: Optional[int] = None
    published_year: Optional[int] = None
    title_ja: Optional[str] = None
    title_en: Optional[str] = None
    official_url: Optional[str] = None
    bgg_url: Optional[str] = None
    bga_url: Optional[str] = None
    amazon_url: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


SearchResult = GameDetail
