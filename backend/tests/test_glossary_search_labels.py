from app.models.concept_taxonomy import GameConceptReference, RuleConceptReference
from app.services.concept_taxonomy import ConceptTaxonomyService


def test_japanese_glossary_includes_canonical_english_label_for_search():
    reference = GameConceptReference(
        concept_id="player-action.bid",
        concept_type="player_action",
        usage_role="glossary",
        preferred_labels={"ja": "ビッド", "en": "Bid"},
        alternate_labels={"ja": ["入札"], "en": ["Bidding"]},
    )

    aliases = ConceptTaxonomyService._glossary_aliases(reference, "ja", "ビッド")

    assert aliases == ["入札", "Bid", "Bidding"]


def test_english_glossary_does_not_mix_unrequested_language_labels():
    reference = GameConceptReference(
        concept_id="player-action.bid",
        concept_type="player_action",
        usage_role="glossary",
        preferred_labels={"ja": "ビッド", "en": "Bid"},
        alternate_labels={"ja": ["入札"], "en": ["Bidding"]},
    )

    aliases = ConceptTaxonomyService._glossary_aliases(reference, "en", "Bid")

    assert aliases == ["Bidding"]


def test_rule_reference_preserves_existing_ruleset_and_source_provenance():
    reference = RuleConceptReference(
        rule_id="round.bid",
        node_type="turn",
        normalized_statement="各ラウンドの開始時にビッドします。",
        reference_kind="defines",
        verification_status="source_bound",
        rule_set_id="ruleset-current",
        source_url="https://example.com/official-rules",
        source_locator="rules:bid",
    )

    assert reference.rule_set_id == "ruleset-current"
    assert reference.source_url == "https://example.com/official-rules"
    assert reference.source_locator == "rules:bid"
