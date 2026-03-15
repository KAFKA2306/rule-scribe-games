from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class GameDetail(BaseSchema):
    id: str
    slug: str | None = None
    title: str
    description: str | None = None
    rules_content: str | None = None
    rules_summary: str | None = None
    image_url: str | None = None
    summary: str | None = None
    structured_data: "StructuredData | None" = None
    source_url: str | None = None
    affiliate_urls: dict[str, str | None] | None = None
    view_count: int | None = 0
    search_count: int | None = 0
    data_version: int | None = 0
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
    min_players: int | None = None
    max_players: int | None = None
    play_time: int | None = None
    min_age: int | None = None
    published_year: int | None = None
    image_url: str | None = None
    official_url: str | None = None
    bgg_url: str | None = None
    structured_data: "StructuredData | None" = None
    rules_content: str | None = None
    rules_summary: str | None = None


SearchResult = GameDetail


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


class StrategyTier(BaseSchema):
    id: str
    game_slug: str
    tier_rating: str
    strategy_content: str
    author: str | None = None
    created_at: str | None = None
