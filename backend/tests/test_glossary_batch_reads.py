from types import SimpleNamespace

from app.services.concept_taxonomy import ConceptTaxonomyService


class FakeQuery:
    def __init__(self, name, tables, calls):
        self.name = name
        self.tables = tables
        self.calls = calls
        self.filters = []
        self.max_rows = None

    def select(self, *_args):
        return self

    def eq(self, key, value):
        self.filters.append((key, lambda actual, expected=value: actual == expected))
        return self

    def in_(self, key, values):
        allowed = set(values)
        self.filters.append((key, lambda actual, expected=allowed: actual in expected))
        return self

    def limit(self, count):
        self.max_rows = count
        return self

    def execute(self):
        self.calls.append(self.name)
        rows = [
            row for row in self.tables.get(self.name, [])
            if all(predicate(row.get(key)) for key, predicate in self.filters)
        ]
        if self.max_rows is not None:
            rows = rows[:self.max_rows]
        return SimpleNamespace(data=rows)


class FakeClient:
    def __init__(self, tables):
        self.tables = tables
        self.calls = []

    def table(self, name):
        return FakeQuery(name, self.tables, self.calls)


def test_glossary_projection_batches_reads_and_keeps_source_bound_rules(monkeypatch):
    tables = {
        "game_concepts": [
            {"concept_id": "player-action.bid", "usage_role": "glossary", "verification_status": "source_bound", "game_id": "game-1"},
            {"concept_id": "component.special-card", "usage_role": "glossary", "verification_status": "source_bound", "game_id": "game-1"},
        ],
        "concepts": [
            {"concept_id": "player-action.bid", "concept_type": "player_action", "definition": "ビッドの定義"},
            {"concept_id": "component.special-card", "concept_type": "component", "definition": "特殊カードの定義"},
        ],
        "concept_labels": [
            {"concept_id": "player-action.bid", "language_code": "ja", "label_type": "pref", "label": "ビッド"},
            {"concept_id": "player-action.bid", "language_code": "en", "label_type": "pref", "label": "Bid"},
            {"concept_id": "component.special-card", "language_code": "ja", "label_type": "pref", "label": "特殊カード"},
            {"concept_id": "component.special-card", "language_code": "en", "label_type": "pref", "label": "Special Card"},
        ],
        "concept_relations": [],
        "rule_sets": [{"id": "ruleset-1", "game_id": "game-1", "is_active": True}],
        "rule_node_concepts": [
            {"rule_set_id": "ruleset-1", "concept_id": "player-action.bid", "rule_id": "scoring.zero-bid", "reference_kind": "mentions", "verification_status": "verified"},
            {"rule_set_id": "ruleset-1", "concept_id": "component.special-card", "rule_id": "two-player.tigress", "reference_kind": "modifies", "verification_status": "source_bound"},
        ],
        "rule_nodes": [
            {"rule_set_id": "ruleset-1", "rule_id": "scoring.zero-bid", "node_type": "scoring", "normalized_statement": "0ビッドは10倍の得点", "source_locator": "skull-king:rulebook:scoring", "metadata": {}},
            {"rule_set_id": "ruleset-1", "rule_id": "two-player.tigress", "node_type": "exception", "normalized_statement": "2人戦のTigress", "source_locator": "skull-king:faq:graybeard-tigress", "metadata": {"condition": {"player_count": 2}}},
        ],
    }
    client = FakeClient(tables)
    monkeypatch.setattr("app.services.concept_taxonomy.supabase._get_client", lambda: client)

    result = ConceptTaxonomyService._load_game_concepts(
        {"id": "game-1", "slug": "skull-king"},
        {"game_id": "game-1", "slug": "skull-king"},
    )

    assert result.status == "available"
    by_id = {item.concept_id: item for item in result.concepts}
    bid = by_id["player-action.bid"]
    assert bid.preferred_labels == {"ja": "ビッド", "en": "Bid"}
    assert bid.rule_references[0].rule_id == "scoring.zero-bid"
    assert bid.rule_references[0].verification_status.value == "verified"
    tigress = by_id["component.special-card"].rule_references[0]
    assert tigress.player_count == 2
    assert tigress.source_locator == "skull-king:faq:graybeard-tigress"

    # Two concepts and two rules must not trigger per-item Supabase requests.
    assert len(client.calls) == 8
    assert client.calls.count("rule_sets") == 1
    assert client.calls.count("rule_nodes") == 1
