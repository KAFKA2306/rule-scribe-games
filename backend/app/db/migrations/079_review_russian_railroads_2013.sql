BEGIN;

-- Player-facing success condition:
-- Russian Railroads original 2013 may be search-indexed only after the exact active
-- source-bound RuleSet has nine accepted rule claims and nine supporting bindings.
-- Ultimate Railroads remains edition-boundary context only and is not rule authority.
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'russian-railroads'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Russian Railroads game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND verification_status = 'source_bound'
    AND COALESCE(edition_label, '') = 'Russian Railroads（2013 original）'
    AND COALESCE(revision_label, '') = 'hig-zman-2013-original-en'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Russian Railroads 2013 RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = 'source_bound'
  ) <> 9 THEN
    RAISE EXCEPTION 'Russian Railroads 2013 requires exactly 9 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 9 THEN
    RAISE EXCEPTION 'Russian Railroads 2013 requires exactly 9 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND eb.relation = 'supports'
  ) <> 9 THEN
    RAISE EXCEPTION 'Russian Railroads 2013 requires exactly 9 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Russian Railroads 2013 RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:hig:russian-railroads:rules-en-2013'
  ) THEN
    RAISE EXCEPTION 'Ultimate Railroads or another source must not become 2013 rule authority';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      source_revision = 'Russian Railroads original 2013 English rulebook; Ultimate Railroads changes excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Russian Railroads original 2013 English rulebook; Ultimate Railroads changes excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"original_2013_base_game"}'::jsonb,
      updated_at = now()
  WHERE source_id = 'publisher:hig:russian-railroads:rules-en-2013';
END $$;

COMMIT;
