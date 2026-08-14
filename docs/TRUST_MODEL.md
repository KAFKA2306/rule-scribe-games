# Catalog trust model

`games` records expose three independent trust axes. None may be inferred from another.

## `identity_status`

- `unverified`: title/edition identity has not been resolved against canonical evidence.
- `verified`: the game/edition identity has been resolved.

Identity verification does not imply that rule content was reviewed.

## `source_trust_status`

- `unknown`: no explicit classified source provenance is recorded.
- `publisher_primary`: explicit publisher/designer primary source is recorded.
- `platform_primary`: explicit first-party platform rules/game page is recorded.
- `secondary`: explicit secondary source classification.
- `tertiary`: explicit tertiary source classification.

A URL existing in `official_url`, `bga_url`, or `source_url` is not sufficient by itself to promote source trust. Promotion requires explicit provenance classification in `structured_data.source_documents` or an authenticated manual update.

`official_url` is reserved for publisher/product official URLs. Board Game Arena URLs belong in `bga_url`.

## `content_review_status`

- `ai_draft`: AI-generated or otherwise not independently reviewed content.
- `human_reviewed`: content reviewed against cited evidence by a human/editorial process.
- `publisher_reviewed`: content confirmed by the publisher/rightsholder.

A primary source does not automatically make generated content human-reviewed.

## Legacy `is_official`

`is_official` remains only for backward compatibility. It is not a UI trust signal. The database rejects `is_official=true` unless `identity_status='verified'`, and new generated records always use `false`.

## Conservative migration policy

Existing records are never promoted from a URL/domain heuristic. The migration promotes `source_trust_status` only when `structured_data.source_documents[*].type` explicitly identifies a publisher or platform primary source. Everything else remains `unknown`. Existing content defaults to `ai_draft` unless an explicit generation provenance review status already exists.

Schema changes are tracked under `supabase/migrations/` and should be applied through the Supabase migration workflow rather than ad-hoc remote edits.
