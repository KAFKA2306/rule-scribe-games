from typing import Optional
from pydantic import BaseModel


class GameDetail(BaseModel):
    id: str
    slug: str
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None
    structured_data: Optional[dict] = None
    source_url: Optional[str] = None
    affiliate_urls: Optional[dict] = None
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


SearchResult = GameDetail
