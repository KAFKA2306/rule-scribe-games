import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.rule_graph import (
    RuleEdge,
    RuleGraphReadResponse,
    RuleNode,
    RuleNodeType,
)
from app.routers import games


def _node(rule_id: str, node_type: RuleNodeType, statement: str) -> RuleNode:
    return RuleNode(
        rule_id=rule_id,
        node_type=node_type,
        normalized_statement=statement,
        verification_status="unverified",
    )


def test_condition_effect_relation_is_explicit_and_validated():
    graph = RuleGraphReadResponse(
        status="available",
        game_id="game-1",
        slug="example",
        rule_set_id="set-1",
        nodes=[
            _node("condition.duplicate", RuleNodeType.CONDITION, "A duplicate value is present."),
            _node("effect.bust", RuleNodeType.EFFECT, "Resolve the bust effect."),
        ],
        edges=[
            RuleEdge(
                from_rule_id="condition.duplicate",
                to_rule_id="effect.bust",
                relation_type="condition_effect",
            )
        ],
    )
    assert graph.edges[0].relation_type == "condition_effect"

    with pytest.raises(ValidationError):
        RuleGraphReadResponse(
            status="available",
            game_id="game-1",
            slug="example",
            rule_set_id="set-1",
            nodes=[
                _node("action.draw", RuleNodeType.ACTION, "Draw."),
                _node("effect.bust", RuleNodeType.EFFECT, "Bust."),
            ],
            edges=[
                RuleEdge(
                    from_rule_id="action.draw",
                    to_rule_id="effect.bust",
                    relation_type="condition_effect",
                )
            ],
        )


def test_unknown_graph_fails_closed_without_invented_nodes():
    graph = RuleGraphReadResponse(
        status="not_available",
        game_id="game-1",
        slug="unknown",
    )
    assert graph.rule_set_id is None
    assert graph.nodes == []
    assert graph.edges == []


def test_rule_type_projection_returns_only_requested_canonical_nodes():
    graph = RuleGraphReadResponse(
        status="available",
        game_id="game-1",
        slug="example",
        rule_set_id="set-1",
        nodes=[
            _node("setup.start", RuleNodeType.SETUP, "Prepare the game."),
            _node("score.points", RuleNodeType.SCORING, "Score points."),
            _node("end.game", RuleNodeType.GAME_END, "End the game."),
            _node("exception.tie", RuleNodeType.EXCEPTION, "Resolve a tie."),
        ],
    )

    projected = graph.select_types({RuleNodeType.SCORING, RuleNodeType.EXCEPTION})
    assert [node.rule_id for node in projected.nodes] == ["score.points", "exception.tie"]


class FakeRuleGraphService:
    def __init__(self):
        self.last_rule_set_id = None

    async def get_by_slug(self, slug: str, rule_types=None, rule_set_id=None):
        self.last_rule_set_id = rule_set_id
        if slug == "missing":
            return None
        graph = RuleGraphReadResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            rule_set_id=rule_set_id or "set-1",
            nodes=[
                _node("score.points", RuleNodeType.SCORING, "Score points."),
                _node("end.game", RuleNodeType.GAME_END, "End the game."),
                _node("exception.tie", RuleNodeType.EXCEPTION, "Resolve a tie."),
            ],
        )
        return graph.select_types(set(rule_types or []))


def _app(service=None):
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_rule_graph_service] = lambda: service or FakeRuleGraphService()
    return app


def test_rule_graph_api_can_query_end_scoring_and_exception_types():
    client = TestClient(_app())
    response = client.get(
        "/api/games/example/rule-graph",
        params=[
            ("types", "game_end"),
            ("types", "scoring"),
            ("types", "exception"),
        ],
    )

    assert response.status_code == 200
    assert {node["node_type"] for node in response.json()["nodes"]} == {
        "game_end",
        "scoring",
        "exception",
    }


def test_rule_graph_api_accepts_explicit_ruleset_identity():
    service = FakeRuleGraphService()
    client = TestClient(_app(service))

    response = client.get("/api/games/example/rule-graph", params={"rule_set_id": "bga-ja-v1"})

    assert response.status_code == 200
    assert response.json()["rule_set_id"] == "bga-ja-v1"
    assert service.last_rule_set_id == "bga-ja-v1"


def test_rule_graph_api_returns_404_for_unknown_game():
    client = TestClient(_app())
    response = client.get("/api/games/missing/rule-graph")
    assert response.status_code == 404


def test_versioned_rule_graph_fixtures_validate_all_required_structures():
    fixture_path = Path(__file__).parents[2] / "evaluation" / "rules" / "rule-graph-v1-fixtures.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert payload["version"] == "rule-graph-fixtures-v1"
    assert len(payload["cases"]) >= 5

    names = set()
    for case in payload["cases"]:
        graph = RuleGraphReadResponse.model_validate(case["graph"])
        names.add(case["name"])
        actual_types = {node.node_type.value for node in graph.nodes}
        for expected in case.get("expected_node_types", []):
            assert expected in actual_types
        actual_relations = {edge.relation_type.value for edge in graph.edges}
        for expected in case.get("expected_relations", []):
            assert expected in actual_relations

    assert {
        "ordered-turn-flow",
        "round-end-vs-game-end",
        "flip7-threshold-continues-round-structural",
        "exception-overrides-base",
        "variant-delta",
    }.issubset(names)
