from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class SearchRequest(BaseSchema):
    query: str
    generate: bool = False


class Keyword(BaseSchema):
    term: str
    description: str


class KeyElement(BaseSchema):
    name: str
    type: str
    reason: str


class StructuredData(BaseSchema):
    keywords: list[Keyword] = []
    key_elements: list[KeyElement] = []
    mechanics: list[str] = []
    best_player_count: str | None = None


class GameDetail(BaseSchema):
    id: str
    slug: str | None = None
    title: str
    description: str | None = None
    rules_content: str | None = None
    rules_summary: str | None = None
    rules_confidence: float = 0.5
    setup_summary: str | None = None
    setup_confidence: float = 0.5
    gameplay_summary: str | None = None
    gameplay_confidence: float = 0.5
    end_game_summary: str | None = None
    end_game_confidence: float = 0.5
    image_url: str | None = None
    summary: str | None = None
    structured_data: StructuredData | None = None
    infographics: dict[str, str] | None = None
    source_url: str | None = None
    affiliate_urls: dict[str, str | None] | None = None
    view_count: int | None = 0
    search_count: int | None = 0
    data_version: int = 1
    last_regenerated_at: datetime | None = None
    is_official: bool | None = False
    min_players: int | None = None
    max_players: int | None = None
    play_time: int | None = None
    min_age: int | None = None
    published_year: int | None = None
    title_ja: str | None = None
    title_en: str | None = None
    official_url: str | None = None
    bgg_url: str | None = None
    bga_url: str | None = None
    amazon_url: str | None = None
    audio_url: str | None = None
    strategy_tier: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class GameUpdate(BaseSchema):
    title: str | None = None
    title_ja: str | None = None
    description: str | None = None
    summary: str | None = None
    rules_summary: str | None = None
    rules_confidence: float | None = Field(None, ge=0, le=1)
    setup_summary: str | None = None
    setup_confidence: float | None = Field(None, ge=0, le=1)
    gameplay_summary: str | None = None
    gameplay_confidence: float | None = Field(None, ge=0, le=1)
    end_game_summary: str | None = None
    end_game_confidence: float | None = Field(None, ge=0, le=1)
    min_players: int | None = None
    max_players: int | None = None
    play_time: int | None = None
    min_age: int | None = None
    published_year: int | None = None
    image_url: str | None = None
    official_url: str | None = None
    bgg_url: str | None = None
    structured_data: StructuredData | None = None
    rules_content: str | None = None
    infographics: dict[str, str] | None = None
    data_version: int | None = None
    last_regenerated_at: datetime | None = None


SEARCH_RESULT = GameDetail


class GeneratedGameMetadata(BaseSchema):
    title: str
    title_ja: str | None = None
    summary: str
    description: str
    min_players: int
    max_players: int
    play_time: int
    min_age: int
    rules_content: str
    structured_data: StructuredData
    infographics: dict[str, str] | None = None


class StrategyTier(BaseSchema):
    id: str
    game_slug: str
    tier_rating: str
    strategy_content: str
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
