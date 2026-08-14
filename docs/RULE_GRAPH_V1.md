# Rule Graph v1

Status: canonical contract for Issue #149  
Schema version: `1.0`

## Purpose

`rules_content`, `setup_summary`, `gameplay_summary`, and `end_game_summary` remain presentation/legacy fields. Canonical rules are represented as nodes and typed relations so the same verified rule can power detailed rules, Quick Rules, UGUG, diagrams, and rule-specific API queries.

The graph is fail-closed: missing evidence does not create a rule node. `unknown` and `unverified` are valid states and must not be promoted by inference.

## Identity and provenance boundary

A rule graph belongs to exactly one game edition (`games.id`) and may link to its canonical work (`game_works.id`). `language_code`, `edition_label`, and `source_revision` are copied into the active `rule_set` so edition/language provenance cannot be lost during projection.

Rule nodes may carry `source_claim_ref`, `evidence_ref`, `source_url`, and `source_locator`. These references do not replace the provenance/trust contracts in #71 and #139; they are foreign identifiers that allow those systems to be joined later.

## Node types

| Type | Meaning |
| --- | --- |
| `setup` | Initial preparation rule |
| `phase` | Named structural phase |
| `turn` | Turn/activation structure when the game has one |
| `action` | Player-permitted action |
| `condition` | Predicate that gates a rule |
| `effect` | State transition/result |
| `scoring` | Score/progress rule |
| `round_end` | Round/hand/chapter end |
| `game_end` | Game termination |
| `victory` | Winner/success determination |
| `exception` | Rule that overrides or narrows a base rule |
| `targeting` | Who/what may be selected |
| `conflict_resolution` | Tie/priority/simultaneous conflict resolution |
| `variant` | Optional/alternate rule set delta |

## Edge types

- `contains`: structural membership such as phase -> action.
- `next`: canonical order.
- `condition_effect`: condition -> effect. API validation requires the source node to be `condition` and destination to be `effect`.
- `results_in`: generic causal/state transition relation.
- `overrides`: exception -> base rule.
- `targets`: targeting rule -> target/action/effect.
- `variant_of`: variant -> base rule changed by the variant.
- `requires`: dependency/precondition relation.

## PostgreSQL layout

```mermaid
erDiagram
    GAMES ||--o{ RULE_SETS : edition
    GAME_WORKS ||--o{ RULE_SETS : work
    RULE_SETS ||--o{ RULE_NODES : contains
    RULE_SETS ||--o{ RULE_EDGES : contains
    RULE_NODES ||--o{ RULE_EDGES : from
    RULE_NODES ||--o{ RULE_EDGES : to
```

## API

`GET /api/games/{slug}/rule-graph`

Optional repeated query parameter:

`?types=game_end&types=scoring&types=exception`

Response status is:

- `available`: an active canonical rule set exists.
- `not_available`: the game exists but no canonical rule graph is available, the DB migration is not yet present, or the local fallback DB is in use.

`not_available` MUST contain no rule nodes or edges. It is not an invitation to synthesize them.

## Legacy migration map

| Legacy field | Rule Graph destination |
| --- | --- |
| `setup_summary` | one or more `setup` nodes |
| `gameplay_summary` | `phase` / `turn` / `action` / `condition` / `effect` nodes and ordering edges |
| `end_game_summary` | `game_end` and, when separately evidenced, `victory` nodes |
| scoring paragraphs in `rules_content` | `scoring` nodes |
| FAQ/known exceptions | `exception` + `overrides` |
| player/card target restrictions | `targeting` + `targets` |
| optional modes | `variant` + `variant_of` |

Migration is evidence-gated. Legacy prose without edition/language/source support stays unresolved and is not converted into a verified node.

## Projection rules

Quick Rules and later UGUG/diagram projections consume only graph nodes. Projection code may shorten wording, but it must preserve `rule_id` traceability and may not add factual rules absent from the graph.

## Validation

The Pydantic contract rejects duplicate `rule_id` values, edges referencing missing nodes, malformed `condition_effect` edges, `not_available` responses containing canonical nodes, and unknown node/relation enum values.

The SQL migration adds type checks, endpoint foreign keys, one active rule set per game, and an audit view.

## Primary references

- W3C PROV-O: https://www.w3.org/TR/prov-o/
- W3C SHACL Recommendation: https://www.w3.org/TR/shacl/
