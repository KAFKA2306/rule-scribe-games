from app.services.player_summary import project_player_summary


CANONICAL_RULES = """## セットアップ
- 第1ラウンドは1枚ずつ配り、以後ラウンド数と同じ枚数を配る。
- 手札を確認して、取るトリック数を同時にビッドする。

## ゲーム進行
- ディーラーの左隣から1枚出し、時計回りに続ける。
- 全員が1枚出したら最も強いカードがトリックを取る。

## 終了条件・勝利
- 10ラウンド終了後にゲームを終える。

## 得点
- ビッドを正確に達成したかどうかで得失点する。
"""


def test_source_bound_unreviewed_summary_is_neutralized_and_coach_uses_canonical_rules():
    game = {
        "title": "Forest Shuffle",
        "title_ja": "フォレストシャッフル",
        "summary": "legacy summary",
        "description": "legacy description",
        "content_review_status": "unknown",
        "rules_content": CANONICAL_RULES,
        "setup_summary": "legacy setup",
        "gameplay_summary": "legacy gameplay",
        "end_game_summary": "legacy end",
    }

    projected = project_player_summary(game, source_bound=True)

    assert projected["summary"] == "「フォレストシャッフル」の出典付きルール要約と出典情報を確認できます。"
    assert projected["description"] == projected["summary"]
    assert projected["setup_summary"] == (
        "第1ラウンドは1枚ずつ配り、以後ラウンド数と同じ枚数を配る。 "
        "手札を確認して、取るトリック数を同時にビッドする。"
    )
    assert projected["gameplay_summary"] == (
        "ディーラーの左隣から1枚出し、時計回りに続ける。 "
        "全員が1枚出したら最も強いカードがトリックを取る。"
    )
    assert projected["end_game_summary"] == (
        "10ラウンド終了後にゲームを終える。 ビッドを正確に達成したかどうかで得失点する。"
    )
    assert game["setup_summary"] == "legacy setup"


def test_source_bound_without_canonical_sections_does_not_expose_legacy_rule_summaries():
    game = {
        "title": "Legacy Game",
        "content_review_status": "human_reviewed",
        "rules_content": "## その他\n- canonical text",
        "setup_summary": "legacy setup",
        "gameplay_summary": "legacy gameplay",
        "end_game_summary": "legacy end",
    }

    projected = project_player_summary(game, source_bound=True)

    assert projected["setup_summary"] is None
    assert projected["gameplay_summary"] is None
    assert projected["end_game_summary"] is None


def test_source_bound_human_reviewed_summary_is_preserved():
    game = {
        "title": "Fort",
        "summary": "reviewed summary",
        "description": "reviewed description",
        "content_review_status": "human_reviewed",
        "rules_content": CANONICAL_RULES,
    }

    projected = project_player_summary(game, source_bound=True)

    assert projected["summary"] == "reviewed summary"
    assert projected["description"] == "reviewed description"
    assert projected["setup_summary"] is not None


def test_source_bound_publisher_reviewed_summary_is_preserved():
    game = {
        "title": "Papayoo",
        "summary": "publisher summary",
        "content_review_status": "publisher_reviewed",
        "rules_content": CANONICAL_RULES,
    }

    projected = project_player_summary(game, source_bound=True)

    assert projected["summary"] == "publisher summary"
    assert projected["gameplay_summary"] is not None


def test_non_source_bound_rules_and_legacy_rule_summaries_are_hidden():
    game = {
        "title": "Legacy Game",
        "summary": "legacy summary",
        "description": "legacy description",
        "content_review_status": "unknown",
        "rules_content": CANONICAL_RULES,
        "setup_summary": "legacy setup",
    }

    projected = project_player_summary(game, source_bound=False)

    assert projected["rules_content"] is None
    assert projected["setup_summary"] is None
    assert projected["summary"] == "legacy summary"
