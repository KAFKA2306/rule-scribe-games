from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    # AI生成データに含まれる _debug_info などの未定義フィールドを
    # エラーにせず黙って無視するための設定 (Pydantic v2推奨記法)
    model_config = ConfigDict(extra="ignore")


class GameDetail(BaseSchema):
    # 既存ロジックに従い、IDとSlugは必須項目として維持
    id: str
    slug: str
    title: str

    # 以下、Optionalフィールド
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    affiliate_urls: Optional[Dict[str, Any]] = None

    # カウンターやフラグのデフォルト値
    view_count: Optional[int] = 0
    search_count: Optional[int] = 0
    data_version: Optional[int] = 0
    is_official: Optional[bool] = False

    # スペック情報
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    play_time: Optional[int] = None
    min_age: Optional[int] = None
    published_year: Optional[int] = None

    # 言語・リンク情報
    title_ja: Optional[str] = None
    title_en: Optional[str] = None
    official_url: Optional[str] = None
    bgg_url: Optional[str] = None
    bga_url: Optional[str] = None
    amazon_url: Optional[str] = None
    audio_url: Optional[str] = None


SearchResult = GameDetail
