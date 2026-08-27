BEGIN;

-- Player-facing success condition:
-- CATAN Standard Edition (GP Games 2026 renewal) may be search-indexed only after the
-- exact active Japanese product RuleSet has eleven accepted rule claims and eleven
-- supporting bindings. Rule authority is limited to CATAN's current 6th-edition base
-- rulebook; the GP Games 2026 product page establishes the Japanese product identity.
-- Older Japanese editions, expansions, and 5-6 player rules remain excluded.
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'catan'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Catan game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'GP Games 日本語版 スタンダード版 (2026リニューアル)'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = '2026-renewed-6e'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Catan 2026 Japanese RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 11 THEN
    RAISE EXCEPTION 'Catan 2026 requires exactly 11 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 11 THEN
    RAISE EXCEPTION 'Catan 2026 requires exactly 11 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
  ) <> 11 THEN
    RAISE EXCEPTION 'Catan 2026 requires exactly 11 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Catan 2026 RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:catan:catan:6e-rulebook'
  ) THEN
    RAISE EXCEPTION 'Only the CATAN 6th-edition base rulebook may be rule authority for Catan 2026';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:gp:catan:2026-standard-product'
      AND url = 'https://www.gp-inc.jp/boardgame_catan_new_s.html'
      AND revision_label = '2026-renewed'
      AND publisher_name = 'GP Games / CATAN GmbH'
  ) THEN
    RAISE EXCEPTION 'GP Games Catan 2026 product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:catan:catan:6e-rulebook'
      AND revision_label = '6th-edition-2025'
      AND publisher_name = 'CATAN GmbH / CATAN Studio'
      AND source_type = 'publisher_rulebook'
  ) THEN
    RAISE EXCEPTION 'CATAN current 6th-edition base rulebook source is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:catan:catan:6e-rulebook',
      'publisher:catan:catan:basegame-faq',
      'publisher:gp:catan:2026-standard-product'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Catan 2026 RuleSet must preserve product, base rulebook, and FAQ source distinctions';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      published_year = 2026,
      source_revision = 'GP Games Japanese Standard Edition 2026 renewal identity + CATAN current 6th-edition base rules; older Japanese editions, expansions, and 5-6 player rules excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'GP Games Japanese Standard Edition 2026 renewal identity + CATAN current 6th-edition base rules; older Japanese editions, expansions, and 5-6 player rules excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"catan_gp_japan_2026_standard_base_game"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:gp:catan:2026-standard-product',
    'publisher:catan:catan:6e-rulebook',
    'publisher:catan:catan:basegame-faq'
  );
END $$;

COMMIT;
