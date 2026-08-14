# Canonical Game Identity Contract

Issue: #90

## Identity levels

`game_works` represents the abstract game/work. `games` remains the concrete edition record used by existing URLs and foreign keys. A work can therefore have multiple editions without mixing their rule content.

Stable external identity is explicit:

- `game_works.bgg_id`: BoardGameGeek boardgame/thing ID (work-level evidence).
- `games.bgg_version_id`: BoardGameGeek version ID (edition-level evidence).
- `games.work_id`: explicit work membership.

A title, localized title, slug, publisher, year, or language is never sufficient by itself to merge records.

## Legacy migration rule

Every existing `games` row becomes its own distinct `game_works` row using the same UUID. This deliberately produces false-positive duplicate candidates instead of destructive false merges. Existing BGG work IDs are backfilled only when a numeric ID is already present in the stored `bgg_url`; missing IDs remain missing.

No legacy row is deleted or merged by the migration.

## Edition metadata

The edition record can carry:

- `edition_label`
- `language_code`
- `publisher`
- `bgg_version_id`
- `source_revision`
- `generated_from_source_revision`
- `identity_status`: `unverified`, `verified`, or `needs_review`

`game_generation_freshness` reports whether generated content is current, stale, or lacks revision evidence.

## Names and URLs

`game_title_aliases` stores display/search names separately from identity. Existing `title`, `title_ja`, and `title_en` are backfilled as aliases.

`game_slug_aliases` is URL history. Changing `games.slug` automatically reserves the old slug for the same game, so an old public URL can still resolve to the canonical edition. A slug already reserved by another game's alias cannot be reused.

## Duplicate handling

`game_identity_duplicate_candidates` surfaces normalized-title collisions for review. It is an audit queue, not an automatic merge list.

Resolution order:

1. Exact verified edition external ID -> same edition.
2. Exact verified work external ID -> same work, but editions remain separate unless edition identity is also proven.
3. Conflicting verified work IDs -> distinct works.
4. Title/alias similarity without stable external evidence -> `needs_review`; never merge automatically.

## Source provenance

`source_revision` identifies the currently observed upstream revision. `generated_from_source_revision` records which revision produced the current generated rules. A mismatch is `stale`; missing evidence remains explicitly unknown.

## Audit

`game_identity_audit_summary` reports total games, total works, BGG coverage, missing language/source revision, and duplicate-title groups. Production migration acceptance requires row-count preservation and review of this summary plus duplicate candidates.
