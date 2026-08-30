from typing import Any

REVIEWED_SUMMARY_STATUSES = {"human_reviewed", "publisher_reviewed"}
TRUSTED_INFOGRAPHICS_SOURCES = {"official_publisher", "authorized_partner"}
DIRECTORY_UNVERIFIED_SUMMARY = "概要は確認中です。"
_LEGACY_RULE_SUMMARY_FIELDS = ("setup_summary", "gameplay_summary", "end_game_summary")


def project_player_summary(game: dict[str, Any], *, source_bound: bool) -> dict[str, Any]:
    """Project player-facing fields without treating legacy game-row rules as authority."""
    projected = {**game, **{field: None for field in _LEGACY_RULE_SUMMARY_FIELDS}}
    infographics_verified = bool(
        source_bound
        and projected.get("infographics")
        and projected.get("source_url")
        and projected.get("source_trust") in TRUSTED_INFOGRAPHICS_SOURCES
    )
    projected = {
        **projected,
        "infographics_reviewed": infographics_verified,
        "infographics_source_url": projected.get("source_url") if infographics_verified else None,
    }

    if not source_bound:
        return {**projected, "rules_content": None}

    if projected.get("content_review_status") in REVIEWED_SUMMARY_STATUSES:
        return projected

    title = projected.get("title_ja") or projected.get("title") or "このゲーム"
    neutral = f"「{title}」の出典付きルール要約と出典情報を確認できます。"
    return {**projected, "summary": neutral, "description": neutral}


def project_directory_summary(game: dict[str, Any]) -> dict[str, Any]:
    """Hide unverified catalog prose at the discovery decision point."""
    if (
        game.get("identity_status") == "verified"
        and game.get("content_review_status") in REVIEWED_SUMMARY_STATUSES
    ):
        return game

    return {
        **game,
        "summary": DIRECTORY_UNVERIFIED_SUMMARY,
        "description": DIRECTORY_UNVERIFIED_SUMMARY,
    }
