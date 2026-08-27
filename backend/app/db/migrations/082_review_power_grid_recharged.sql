BEGIN;

-- Player-facing success condition:
-- 電力会社 充電完了！ 完全日本語版 (2019 Recharged) may be search-indexed only
-- after the exact active Japanese physical RuleSet has ten source-bound RuleNodes,
-- ten accepted rule claims, and ten supporting evidence bindings. Rule authority is
-- limited to the 2F-Spiele Recharged base rulebook; Arclight establishes the Japanese
-- product identity. Classic 2004, Deluxe, card game, Outpost, expansions, promos, and
-- map-specific expansion rules remain excluded.
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'power-grid'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Power Grid game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = '電力会社 充電完了！ 完全日本語版 (2019 Recharged)'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = '2019-recharged'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Power Grid 2019 Recharged Japanese RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 10 THEN
    RAISE EXCEPTION 'Power Grid Recharged requires exactly 10 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 10 THEN
    RAISE EXCEPTION 'Power Grid Recharged requires exactly 10 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
  ) <> 10 THEN
    RAISE EXCEPTION 'Power Grid Recharged requires exactly 10 supporting evidence bindings';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    LEFT JOIN public.claims c
      ON c.claim_id = rn.source_claim_ref
      AND c.rule_set_id = rn.rule_set_id
      AND c.lifecycle_status = 'accepted'
    LEFT JOIN public.evidence_bindings eb
      ON eb.binding_id = rn.evidence_ref
      AND eb.claim_id = c.claim_id
      AND eb.relation = 'supports'
    WHERE rn.rule_set_id = v_ruleset_id
      AND (c.claim_id IS NULL OR eb.binding_id IS NULL)
  ) THEN
    RAISE EXCEPTION 'Every Power Grid Recharged RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:2f:power-grid-recharged:rulebook'
  ) THEN
    RAISE EXCEPTION 'Only the 2F-Spiele Recharged base rulebook may be rule authority for Power Grid Recharged';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:arclight:power-grid-recharged:product'
      AND url = 'https://arclightgames.jp/product/%E9%9B%BB%E5%8A%9B%E4%BC%9A%E7%A4%BE%E5%85%85%E9%9B%BB%E5%AE%8C%E4%BA%86%EF%BC%81/'
      AND revision_label = '2019-07-18'
      AND publisher_name = 'Arclight Games'
      AND source_type = 'publisher_product_page'
  ) THEN
    RAISE EXCEPTION 'Arclight Power Grid Recharged Japanese product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:2f:power-grid-recharged:product'
      AND revision_label = '2019-recharged'
      AND publisher_name = '2F-Spiele'
      AND source_type = 'publisher_product_page'
  ) THEN
    RAISE EXCEPTION '2F-Spiele Power Grid Recharged product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:2f:power-grid-recharged:rulebook'
      AND revision_label = '2019-recharged'
      AND publisher_name = '2F-Spiele'
      AND source_type = 'publisher_rulebook'
  ) THEN
    RAISE EXCEPTION '2F-Spiele Power Grid Recharged base rulebook source is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:arclight:power-grid-recharged:product',
      'publisher:2f:power-grid-recharged:product',
      'publisher:2f:power-grid-recharged:rulebook'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Power Grid Recharged RuleSet must preserve Japanese product, Recharged product, and base rulebook source distinctions';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      published_year = 2019,
      source_revision = 'Arclight Japanese Recharged product identity + 2F-Spiele 2019 Recharged base rules; classic 2004, Deluxe, card game, Outpost, expansions, promos, and map-specific expansion rules excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Arclight Japanese Recharged product identity + 2F-Spiele 2019 Recharged base rules; classic 2004, Deluxe, card game, Outpost, expansions, promos, and map-specific expansion rules excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"power_grid_recharged_2019_japanese_base_game"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:arclight:power-grid-recharged:product',
    'publisher:2f:power-grid-recharged:product',
    'publisher:2f:power-grid-recharged:rulebook'
  );
END $$;

COMMIT;
