BEGIN;

-- Player-facing success condition:
-- Splendor (2024 revised Japanese edition) may be search-indexed only after the exact
-- active source-bound RuleSet has fourteen accepted rule claims and fourteen supporting
-- bindings, using only the 2024 Hobby Japan product identity and SPACE Cowboys 2024
-- refreshed base rulebook. Older editions, Duel, and expansions remain excluded.
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'splendor'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Splendor game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND verification_status = 'source_bound'
    AND COALESCE(edition_label, '') = 'ホビージャパン日本語版 改訂版 (2024)'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Splendor 2024 Japanese RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = 'source_bound'
  ) <> 14 THEN
    RAISE EXCEPTION 'Splendor 2024 requires exactly 14 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 14 THEN
    RAISE EXCEPTION 'Splendor 2024 requires exactly 14 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND eb.relation = 'supports'
  ) <> 14 THEN
    RAISE EXCEPTION 'Splendor 2024 requires exactly 14 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Splendor 2024 RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id NOT IN (
        'publisher:hobbyjapan:splendor:2024-revised-product',
        'publisher:space-cowboys:splendor:2024-refresh-rulebook'
      )
  ) THEN
    RAISE EXCEPTION 'Older Splendor editions, Duel, expansions, or another source must not become 2024 base-game rule authority';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:hobbyjapan:splendor:2024-revised-product'
      AND url = 'https://hobbyjapan.games/splendor/'
      AND revision_label = '2024-07'
  ) THEN
    RAISE EXCEPTION 'Hobby Japan Splendor 2024 product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:space-cowboys:splendor:2024-refresh-rulebook'
      AND revision_label = '2024-refresh'
  ) THEN
    RAISE EXCEPTION 'SPACE Cowboys Splendor 2024 refreshed rulebook source is required';
  END IF;

  -- The lightweight migration-replay fixture intentionally omits review-only columns.
  -- Keep the production mutation idempotent without coupling that fixture to the full app schema.
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'games'
      AND column_name = 'content_review_status'
  ) THEN
    EXECUTE
      'UPDATE public.games SET content_review_status = $1, published_year = $2, source_revision = $3, updated_at = now() WHERE id = $4'
    USING
      'human_reviewed',
      2024,
      'Hobby Japan Japanese revised edition released 2024-07 + SPACE Cowboys 2024 refreshed base rulebook; older edition, Duel, and expansions excluded; human-reviewed 2026-08-28',
      v_game_id;
  ELSE
    UPDATE public.games
    SET published_year = 2024,
        source_revision = 'Hobby Japan Japanese revised edition released 2024-07 + SPACE Cowboys 2024 refreshed base rulebook; older edition, Duel, and expansions excluded; human-reviewed 2026-08-28',
        updated_at = now()
    WHERE id = v_game_id;
  END IF;

  UPDATE public.rule_sets
  SET source_revision = 'Hobby Japan Japanese revised edition released 2024-07 + SPACE Cowboys 2024 refreshed base rulebook; older edition, Duel, and expansions excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"splendor_2024_revised_base_game"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:hobbyjapan:splendor:2024-revised-product',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook'
  );
END $$;

COMMIT;
