from typing import Any

REVIEWED_SUMMARY_STATUSES = {"human_reviewed", "publisher_reviewed"}
DIRECTORY_UNVERIFIED_SUMMARY = "概要は確認中です。"


def project_player_summary(game: dict[str, Any], *, source_bound: bool) -> dict[str, Any]:
    """Project player-facing summary fields without changing stored catalog data."""
    if not source_bound:
        return game

    if game.get("content_review_status") in REVIEWED_SUMMARY_STATUSES:
        return game

    title = game.get("title_ja") or game.get("title") or "このゲーム"
    neutral = f"「{title}」の出典付きルール要約と出典情報を確認できます。"
    return {**game, "summary": neutral, "description": neutral}


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
