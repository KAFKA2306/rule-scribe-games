from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class GameDetail(BaseSchema):
    id: str
    slug: Optional[str] = None
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


class GameUpdate(BaseSchema):
    title: Optional[str] = None
    title_ja: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    play_time: Optional[int] = None
    min_age: Optional[int] = None
    published_year: Optional[int] = None
    image_url: Optional[str] = None
    official_url: Optional[str] = None
    bgg_url: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    rules_content: Optional[str] = None


SearchResult = GameDetail


# --- AI Generation Models ---

class Keyword(BaseSchema):
    term: str
    description: str


class KeyElement(BaseSchema):
    name: str
    type: str  # e.g. "Card", "Token", "Action"
    reason: str


class StructuredData(BaseSchema):
    keywords: List[Keyword] = []
    key_elements: List[KeyElement] = []
    # Add other flexible fields if needed, but these 2 are strict for Frontend
    mechanics: List[str] = []
    best_player_count: Optional[str] = None


class GeneratedGameMetadata(BaseSchema):
    title: str
    title_ja: Optional[str] = None
    summary: str
    description: str
    min_players: int
    max_players: int
    play_time: int
    min_age: int
    rules_content: str  # Markdown
    structured_data: StructuredData

