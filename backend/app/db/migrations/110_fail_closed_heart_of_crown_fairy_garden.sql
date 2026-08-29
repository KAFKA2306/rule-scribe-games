BEGIN;

-- Player-facing success condition:
-- /games/heart-of-crown-fairy-garden must not present unsourced rules,
-- edition-specific metadata, or an affiliate purchase link while its exact
-- physical edition and first-party rules remain unverified.
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'heart-of-crown-fairy-garden';

  IF v_game_id IS NULL THEN
    IF current_database() = 'source_bound_ruleset_test' THEN
      RAISE NOTICE 'heart-of-crown-fairy-garden is not part of the fixture; skipping migration';
      RETURN;
    END IF;
    RAISE EXCEPTION 'heart-of-crown-fairy-garden row is missing';
  END IF;

  SELECT count(*) INTO v_ruleset_count
  FROM public.rule_sets
  WHERE game_id = v_game_id;

  IF v_ruleset_count <> 0 THEN
    RAISE EXCEPTION 'heart-of-crown-fairy-garden unexpectedly has % RuleSets; inspect source bindings before changing legacy data', v_ruleset_count;
  END IF;
END $$;

UPDATE public.games
SET
  edition_label = NULL,
  language_code = NULL,
  publisher = NULL,
  is_official = false,
  identity_status = 'unverified',
  identity_source = NULL,
  source_trust = 'unknown',
  content_review_status = 'review_required',
  source_revision = 'exact physical edition and first-party rules not source-bound; legacy unsourced content removed; audited 2026-08-29',
  description = NULL,
  summary = NULL,
  rules = '{}'::jsonb,
  rules_content = NULL,
  structured_data = '{}'::jsonb,
  setup_summary = NULL,
  gameplay_summary = NULL,
  end_game_summary = NULL,
  min_players = NULL,
  max_players = NULL,
  play_time = NULL,
  play_time_min_minutes = NULL,
  play_time_max_minutes = NULL,
  min_age = NULL,
  published_year = NULL,
  source_url = NULL,
  official_url = NULL,
  amazon_url = NULL,
  updated_at = now()
WHERE slug = 'heart-of-crown-fairy-garden';

DO $$
BEGIN
  IF current_database() = 'source_bound_ruleset_test'
     AND NOT EXISTS (SELECT 1 FROM public.games WHERE slug = 'heart-of-crown-fairy-garden') THEN
    RETURN;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE slug = 'heart-of-crown-fairy-garden'
      AND identity_status = 'unverified'
      AND source_trust = 'unknown'
      AND content_review_status = 'review_required'
      AND identity_source IS NULL
      AND source_url IS NULL
      AND official_url IS NULL
      AND amazon_url IS NULL
      AND description IS NULL
      AND summary IS NULL
      AND rules = '{}'::jsonb
      AND rules_content IS NULL
      AND structured_data = '{}'::jsonb
      AND setup_summary IS NULL
      AND gameplay_summary IS NULL
      AND end_game_summary IS NULL
      AND min_players IS NULL
      AND max_players IS NULL
      AND play_time IS NULL
      AND play_time_min_minutes IS NULL
      AND play_time_max_minutes IS NULL
      AND min_age IS NULL
      AND published_year IS NULL
  ) THEN
    RAISE EXCEPTION 'heart-of-crown-fairy-garden did not reach fail-closed state';
  END IF;
END $$;

COMMIT;
