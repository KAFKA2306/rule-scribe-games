from pathlib import Path

from app.models.rule_graph import RuleNode, RuleNodeType


MIGRATION = (
    Path(__file__).parents[1]
    / "app"
    / "db"
    / "migrations"
    / "016_seed_skull_king_rule_concepts.sql"
)

SOURCE_URL = "https://www.grandpabecksgames.com/pages/skull-king"

EXPECTED_LINKS = {
    "skull-king.action.bid": "player-action.bid",
    "skull-king.turn.trick": "rule-pattern.trick",
    "skull-king.conflict.trump": "rule-pattern.trump-suit",
    "skull-king.exception.special-card": "component.special-card",
}


def sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_pilot_rule_ids_and_types_fit_rule_graph_contract():
    nodes = [
        RuleNode(
            rule_id="skull-king.action.bid",
            node_type=RuleNodeType.ACTION,
            normalized_statement="各ラウンドで獲得すると予想するトリック数をビッドする。",
            verification_status="source_bound",
            source_url=SOURCE_URL,
        ),
        RuleNode(
            rule_id="skull-king.turn.trick",
            node_type=RuleNodeType.TURN,
            normalized_statement="各プレイヤーが1枚ずつカードを出してトリックを解決する。",
            verification_status="source_bound",
            source_url=SOURCE_URL,
        ),
        RuleNode(
            rule_id="skull-king.conflict.trump",
            node_type=RuleNodeType.CONFLICT_RESOLUTION,
            normalized_statement="黒のJolly Rogerスートは通常スートより強い。",
            verification_status="source_bound",
            source_url=SOURCE_URL,
        ),
        RuleNode(
            rule_id="skull-king.exception.special-card",
            node_type=RuleNodeType.EXCEPTION,
            normalized_statement="特殊カードはフォロー義務にかかわらずプレイできる。",
            verification_status="source_bound",
            source_url=SOURCE_URL,
        ),
    ]
    assert {node.rule_id for node in nodes} == set(EXPECTED_LINKS)
    assert all(node.verification_status.value == "source_bound" for node in nodes)


def test_migration_links_every_seeded_glossary_concept():
    body = sql()
    for rule_id, concept_id in EXPECTED_LINKS.items():
        assert rule_id in body
        assert concept_id in body
    assert body.count(SOURCE_URL) >= 4
    assert "INSERT INTO public.rule_node_concepts" in body


def test_migration_is_replay_safe_and_preserves_stronger_verification():
    body = sql()
    assert "WHERE NOT EXISTS (" in body
    assert "ON CONFLICT (rule_set_id, rule_id) DO UPDATE" in body
    assert "ON CONFLICT (rule_set_id, rule_id, concept_id, reference_kind) DO UPDATE" in body
    assert "WHEN public.rule_nodes.verification_status = 'verified' THEN 'verified'" in body
    assert "WHEN public.rule_node_concepts.verification_status = 'verified' THEN 'verified'" in body
    assert "WHEN target.verification_status = 'verified' THEN 'verified'" in body


def test_pilot_remains_source_bound_instead_of_self_verifying():
    body = sql()
    assert body.count("'source_bound'") >= 3
    assert "source_locator" in body
    assert "Current English rulebook" in body
    assert "pilot', 'skull-king-concept-link-v1" in body
