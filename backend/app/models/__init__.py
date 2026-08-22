from datetime import datetime
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_validator

IdentityStatus = Literal["unverified", "verified", "needs_review"]
SourceTrust = Literal["unknown", "official_publisher", "authorized_partner", "third_party"]
ContentReviewStatus = Literal["unknown", "ai_draft", "review_required", "human_reviewed", "publisher_reviewed"]


def validate_bga_url(value: str | None) -> str | None:
    """Accept only canonical HTTPS Board Game Arena links."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "boardgamearena.com" or host.endswith(".boardgamearena.com")):
        raise ValueError("bga_url must be an HTTPS URL on boardgamearena.com")
    return value


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Keyword(BaseSchema):
    term: str
    description: str


class KeyElement(BaseSchema):
    name: str
    type: str
    reason: str


class PersonaReview(BaseSchema):
    persona: str
    review_text: str
    rating: float


class GenerationProvenance(BaseSchema):
    model: str
    prompt_version: str
    golden_version: str
    source_bound: bool
    content_review_status: ContentReviewStatus = "ai_draft"


class StructuredData(BaseSchema):
    keywords: list[Keyword] = []
    key_elements: list[KeyElement] = []
    mechanics: list[str] = []
    best_player_count: str | None = None
    pro_tips: list[str] = []
    rule_mistakes: list[str] = []
    strategy_analysis: str | None = None
    persona_reviews: list[PersonaReview] = []
    generation_provenance: GenerationProvenance | None = None


class GameDetail(BaseSchema):
    id: Any
    slug: str | None = None
    work_id: Any | None = None
    identity_status: IdentityStatus = "unverified"
    identity_source: str | None = None
    title: str
    description: str | None = None
    rules_content: str | None = None
    rules_summary: str | None = None
    setup_summary: str | None = None
    gameplay_summary: str | None = None
    end_game_summary: str | None = None
    image_url: str | None = None
    summary: str | None = None
    structured_data: StructuredData | None = None
    infographics: dict[str, str] | None = None
    source_url: str | None = None
    source_trust: SourceTrust = "unknown"
    content_review_status: ContentReviewStatus = "unknown"
    affiliate_urls: dict[str, str | None] | None = None
    view_count: int | None = 0
    search_count: int | None = 0
    data_version: int = 1
    last_regenerated_at: datetime | None = None
    min_players: int | None = None
    max_players: int | None = None
    play_time: int | None = None
    min_age: int | None = None
    published_year: int | None = None
    title_ja: str | None = None
    title_en: str | None = None
    bgg_url: str | None = None
    bga_url: str | None = None
    amazon_url: str | None = None
    audio_url: str | None = None
    strategy_tier: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    _validate_bga_url = field_validator("bga_url")(validate_bga_url)


class GameUpdate(BaseSchema):
    title: str | None = None
    title_ja: str | None = None
    description: str | None = None
    summary: str | None = None
    rules_summary: str | None = None
    setup_summary: str | None = None
    gameplay_summary: str | None = None
    end_game_summary: str | None = None
    min_players: int | None = None
    max_players: int | None = None
    play_time: int | None = None
    min_age: int | None = None
    published_year: int | None = None
    image_url: str | None = None
    source_url: str | None = None
    source_trust: SourceTrust | None = None
    content_review_status: ContentReviewStatus | None = None
    bgg_url: str | None = None
    bga_url: str | None = None
    structured_data: StructuredData | None = None
    rules_content: str | None = None
    infographics: dict[str, str] | None = None
    data_version: int | None = None
    last_regenerated_at: datetime | None = None

    _validate_bga_url = field_validator("bga_url")(validate_bga_url)


SEARCH_RESULT = GameDetail


class StrategyTier(BaseSchema):
    id: str
    game_slug: str
    tier_rating: str
    strategy_content: str
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class GameListResponse(BaseSchema):
    games: list[GameDetail]
    total: int
    limit: int
    offset: int
