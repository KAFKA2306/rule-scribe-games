from app.services.player_summary import project_player_summary


def test_source_bound_unreviewed_summary_is_neutralized():
    game = {
        "title": "Forest Shuffle",
        "title_ja": "フォレストシャッフル",
        "summary": "legacy summary",
        "description": "legacy description",
        "content_review_status": "unknown",
    }

    projected = project_player_summary(game, source_bound=True)

    assert projected["summary"] == "「フォレストシャッフル」の出典付きルール要約と出典情報を確認できます。"
    assert projected["description"] == projected["summary"]
    assert game["summary"] == "legacy summary"


def test_source_bound_human_reviewed_summary_is_preserved():
    game = {
        "title": "Fort",
        "summary": "reviewed summary",
        "description": "reviewed description",
        "content_review_status": "human_reviewed",
    }

    assert project_player_summary(game, source_bound=True) is game


def test_source_bound_publisher_reviewed_summary_is_preserved():
    game = {
        "title": "Papayoo",
        "summary": "publisher summary",
        "content_review_status": "publisher_reviewed",
    }

    assert project_player_summary(game, source_bound=True) is game


def test_non_source_bound_legacy_summary_is_unchanged():
    game = {
        "title": "Legacy Game",
        "summary": "legacy summary",
        "description": "legacy description",
        "content_review_status": "unknown",
    }

    assert project_player_summary(game, source_bound=False) is game
