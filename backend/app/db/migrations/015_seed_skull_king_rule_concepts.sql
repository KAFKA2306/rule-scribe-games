BEGIN;

-- Source-bound production pilot for Rule Graph v1 <-> Concept Taxonomy v1.
-- Primary source: Grandpa Beck's Games, current Skull King English rulebook.
-- https://www.grandpabecksgames.com/pages/skull-king
--
-- This migration intentionally models only rules already bound to the four
-- canonical glossary concepts seeded by 012_seed_skull_king_glossary_concepts.sql.
-- It does not infer scoring, variants, or other rules beyond this pilot scope.

WITH game_row AS (
  SELECT
    id AS game_id,
    work_id
  FROM public.games
  WHERE slug = 'skull-king'
  LIMIT 1
)
INSERT INTO public.rule_sets (
  game_id,
  work_id,
  version,
  schema_version,
  language_code,
  edition_label,
  source_revision,
  is_active,
  revision_label,
  platform,
  publisher_name,
  status,
  verification_status,
  source_ids
)
SELECT
  game_row.game_id,
  game_row.work_id,
  1,
  '1.0',
  'en',
  'Grandpa Beck''s Games current edition',
  'grandpa-becks-current-rulebook-accessed-2026-08-14',
  true,
  'grandpa-becks-current-rulebook-accessed-2026-08-14',
  'physical',
  'Grandpa Beck''s Games',
  'active',
  'source_bound',
  ARRAY['https://www.grandpabecksgames.com/pages/skull-king']::text[]
FROM game_row
WHERE NOT EXISTS (
  SELECT 1
  FROM public.rule_sets existing
  WHERE existing.game_id = game_row.game_id
    AND COALESCE(existing.edition_label, '') = 'Grandpa Beck''s Games current edition'
    AND COALESCE(existing.language_code, '') = 'en'
    AND COALESCE(existing.platform, '') = 'physical'
    AND COALESCE(existing.revision_label, '') = 'grandpa-becks-current-rulebook-accessed-2026-08-14'
    AND COALESCE(existing.variant_label, '') = ''
    AND existing.version = 1
);

-- Preserve any stronger human verification if this seed is replayed after review.
UPDATE public.rule_sets target
SET
  work_id = games.work_id,
  source_revision = 'grandpa-becks-current-rulebook-accessed-2026-08-14',
  is_active = true,
  status = 'active',
  verification_status = CASE
    WHEN target.verification_status = 'verified' THEN 'verified'
    ELSE 'source_bound'
  END,
  source_ids = ARRAY['https://www.grandpabecksgames.com/pages/skull-king']::text[],
  updated_at = now()
FROM public.games games
WHERE games.slug = 'skull-king'
  AND target.game_id = games.id
  AND COALESCE(target.edition_label, '') = 'Grandpa Beck''s Games current edition'
  AND COALESCE(target.language_code, '') = 'en'
  AND COALESCE(target.platform, '') = 'physical'
  AND COALESCE(target.revision_label, '') = 'grandpa-becks-current-rulebook-accessed-2026-08-14'
  AND COALESCE(target.variant_label, '') = ''
  AND target.version = 1;

WITH target_rule_set AS (
  SELECT rule_sets.id
  FROM public.rule_sets rule_sets
  JOIN public.games games ON games.id = rule_sets.game_id
  WHERE games.slug = 'skull-king'
    AND COALESCE(rule_sets.edition_label, '') = 'Grandpa Beck''s Games current edition'
    AND COALESCE(rule_sets.language_code, '') = 'en'
    AND COALESCE(rule_sets.platform, '') = 'physical'
    AND COALESCE(rule_sets.revision_label, '') = 'grandpa-becks-current-rulebook-accessed-2026-08-14'
    AND COALESCE(rule_sets.variant_label, '') = ''
    AND rule_sets.version = 1
  LIMIT 1
),
seed(rule_id, node_type, normalized_statement, sequence, source_locator) AS (
  VALUES
    (
      'skull-king.action.bid',
      'action',
      '各ラウンドで手札を確認し、そのラウンドで獲得すると予想するトリック数をビッドする。0もビッドできる。',
      10,
      'Current English rulebook, Overview and Key Terms, printed pp.3-4: Bid'
    ),
    (
      'skull-king.turn.trick',
      'turn',
      '各プレイヤーが1枚ずつカードを出し、最も強いカードを出したプレイヤーがトリックを取り、その勝者が次のトリックをリードする。',
      20,
      'Current English rulebook, Key Terms and Game Play, printed p.4: Trick'
    ),
    (
      'skull-king.conflict.trump',
      'conflict_resolution',
      '黒のJolly Rogerスートは切り札で、通常スートより強い。',
      30,
      'Current English rulebook, Key Terms, printed p.4: Trump Suit'
    ),
    (
      'skull-king.exception.special-card',
      'exception',
      '特殊カードは、数字カードのフォロー義務にかかわらずいつでもプレイできる。',
      40,
      'Current English rulebook, Key Terms, printed p.4: Special Cards'
    )
)
INSERT INTO public.rule_nodes (
  rule_set_id,
  rule_id,
  node_type,
  normalized_statement,
  sequence,
  verification_status,
  source_url,
  source_locator,
  metadata
)
SELECT
  target_rule_set.id,
  seed.rule_id,
  seed.node_type,
  seed.normalized_statement,
  seed.sequence,
  'source_bound',
  'https://www.grandpabecksgames.com/pages/skull-king',
  seed.source_locator,
  jsonb_build_object('pilot', 'skull-king-concept-link-v1')
FROM target_rule_set
CROSS JOIN seed
ON CONFLICT (rule_set_id, rule_id) DO UPDATE SET
  node_type = EXCLUDED.node_type,
  normalized_statement = EXCLUDED.normalized_statement,
  sequence = EXCLUDED.sequence,
  verification_status = CASE
    WHEN public.rule_nodes.verification_status = 'verified' THEN 'verified'
    ELSE EXCLUDED.verification_status
  END,
  source_url = EXCLUDED.source_url,
  source_locator = EXCLUDED.source_locator,
  metadata = EXCLUDED.metadata,
  updated_at = now();

WITH target_rule_set AS (
  SELECT rule_sets.id
  FROM public.rule_sets rule_sets
  JOIN public.games games ON games.id = rule_sets.game_id
  WHERE games.slug = 'skull-king'
    AND COALESCE(rule_sets.edition_label, '') = 'Grandpa Beck''s Games current edition'
    AND COALESCE(rule_sets.language_code, '') = 'en'
    AND COALESCE(rule_sets.platform, '') = 'physical'
    AND COALESCE(rule_sets.revision_label, '') = 'grandpa-becks-current-rulebook-accessed-2026-08-14'
    AND COALESCE(rule_sets.variant_label, '') = ''
    AND rule_sets.version = 1
  LIMIT 1
),
links(rule_id, concept_id, reference_kind, source_locator) AS (
  VALUES
    (
      'skull-king.action.bid',
      'player-action.bid',
      'defines',
      'Current English rulebook, Overview and Key Terms, printed pp.3-4: Bid'
    ),
    (
      'skull-king.turn.trick',
      'rule-pattern.trick',
      'defines',
      'Current English rulebook, Key Terms and Game Play, printed p.4: Trick'
    ),
    (
      'skull-king.conflict.trump',
      'rule-pattern.trump-suit',
      'defines',
      'Current English rulebook, Key Terms, printed p.4: Trump Suit'
    ),
    (
      'skull-king.exception.special-card',
      'component.special-card',
      'mentions',
      'Current English rulebook, Key Terms, printed p.4: Special Cards'
    )
)
INSERT INTO public.rule_node_concepts (
  rule_set_id,
  rule_id,
  concept_id,
  reference_kind,
  verification_status,
  source_url,
  source_locator,
  metadata
)
SELECT
  target_rule_set.id,
  links.rule_id,
  links.concept_id,
  links.reference_kind,
  'source_bound',
  'https://www.grandpabecksgames.com/pages/skull-king',
  links.source_locator,
  jsonb_build_object('pilot', 'skull-king-concept-link-v1')
FROM target_rule_set
CROSS JOIN links
ON CONFLICT (rule_set_id, rule_id, concept_id, reference_kind) DO UPDATE SET
  verification_status = CASE
    WHEN public.rule_node_concepts.verification_status = 'verified' THEN 'verified'
    ELSE EXCLUDED.verification_status
  END,
  source_url = EXCLUDED.source_url,
  source_locator = EXCLUDED.source_locator,
  metadata = EXCLUDED.metadata;

COMMIT;
