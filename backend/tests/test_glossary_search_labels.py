from app.models.concept_taxonomy import GameConceptReference
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
