# Concept Taxonomy v1

Status: canonical contract for Issue #150  
Schema version: `1.0`

## Purpose

Board-game mechanics, components, resources, states, player actions, information structures, interaction patterns, and rule patterns are canonical concepts identified by stable `concept_id` values. Human-readable labels are attributes of a concept, never its identity.

This taxonomy does not seed unverified board-game concepts. Legacy `structured_data.mechanics` and `keywords` are migration inputs only; they may resolve to an existing concept when a label match is unique, otherwise they remain ambiguous/unresolved.

## SKOS alignment

W3C SKOS separates concepts from lexical labels and defines `prefLabel`, `altLabel`, direct hierarchical `broader` / `narrower` relations, and associative `related` relations. Concept Taxonomy v1 adopts those semantics without requiring RDF as the storage engine.

Canonical storage therefore provides:

- one stable concept identifier independent of labels;
- at most one preferred label per concept/language;
- any number of alternate labels;
- direct `broader`, `narrower`, and `related` relations;
- no automatic transitive assertion as a direct relation;
- validation that a pair is not both hierarchical and `related`.

## Concept types

- `mechanic`
- `component`
- `resource`
- `state`
- `player_action`
- `information_structure`
- `interaction_pattern`
- `rule_pattern`

Different semantic types remain distinct even when they share a display word.

## Lifecycle

`active` is the normal state. `deprecated` remains addressable for historical references. `merged` requires `replaced_by_concept_id`; old IDs remain resolvable and can project to the replacement. Renaming a preferred label never changes `concept_id`.

## Verification and provenance

Concepts, concept relations, game links, and rule links use `unknown`, `source_bound`, or `verified`. A relation extracted or inferred without evidence does not become verified. `source_url` and `source_locator` connect taxonomy assertions to the repository's broader evidence/trust contracts.

## Game linkage

`game_concepts` links a canonical game edition to a concept by stable ID with a usage role:

- `core`: central to describing the game;
- `supporting`: materially present but not central;
- `glossary`: useful as a term definition/projection.

The GamePage and later Mechanical DNA implementation consume concept IDs rather than compare labels.

## Rule Graph linkage and backlinks

`rule_node_concepts` is the canonical bridge between Rule Graph v1 and Concept Taxonomy v1. It links one `rule_node` to one stable `concept_id` with a `reference_kind`:

- `mentions`: the rule uses the concept;
- `defines`: the rule gives a game-specific definition or interpretation;
- `requires`: understanding/applying the rule depends on the concept;
- `modifies`: the rule changes the normal behavior of the concept for this game/variant.

The global Concept definition and a game-specific RuleNode statement are deliberately separate. For example, a general definition of `trick` does not contain Skull King-specific card resolution. The game-specific rule points back to the same concept instead.

This bridge enables deterministic backlinks:

`Concept -> game_concepts -> Game`

`Concept -> rule_node_concepts -> RuleNode -> RuleSet -> Game`

and the reverse direction:

`RuleNode -> rule_node_concepts -> Concept`.

## Linked glossary projection

The glossary is a projection, not another truth store.

- `GET /api/games/{slug}/glossary?language_code=ja` returns stable concept IDs, localized labels, aliases, global definitions, related concept IDs, and rule references for the selected game.
- `GET /api/concepts/{concept_id}` returns the canonical concept, semantic relations, and game/rule backlinks.
- `GET /api/games/{slug}/concepts` exposes the broader game-to-concept projection.

The GamePage uses the canonical glossary when available. Selecting a term opens an inspector showing the stable ID, definition, related concepts, the rules in the current game that reference it, and other games using the concept. If canonical mappings are not available during migration, the existing legacy keyword display remains visible; the UI does not invent canonical mappings.

A later Presentation Projection issue may add a dedicated `/concepts/{concept_id}` page and richer navigation, but the linked identity/backlink contract is owned here.

## Legacy migration

The deterministic resolver applies Unicode NFKC, case folding, and whitespace/hyphen/underscore normalization. A legacy term maps only when exactly one non-merged concept label matches. Zero matches remain unresolved. Multiple matches remain ambiguous and require review. The resolver never creates a new concept or promotes verification state.

## Schema.org projection

For public structured data, `concept_id` can project to Schema.org `DefinedTerm.termCode`, the preferred label to `name`, aliases to `alternateName`, definition to `description`, and the taxonomy scheme to `inDefinedTermSet`. This is a derived web projection, not the canonical database identity.

## Primary references

- W3C SKOS Reference: https://www.w3.org/TR/skos-reference/
- Schema.org DefinedTerm: https://schema.org/DefinedTerm
- Schema.org DefinedTermSet: https://schema.org/DefinedTermSet
