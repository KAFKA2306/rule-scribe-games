BEGIN;

-- Player-facing success condition:
-- The ambiguous historical /games/heart-of-crown row must not present
-- Second Edition identity, rule text, edition-specific metadata, or a Second
-- Edition affiliate link while its exact physical edition remains unverified.
-- The verified Second Edition row remains the only canonical Second Edition
-- identity, and it remains review_required until an exact first-party physical
-- rulebook is source-bound.

DO $$
DECLARE
  generic_game_id uuid;
  canonical_game_id uuid;
  generic_ruleset_count integer;
BEGIN
  SELECT id INTO generic_game_id
  FROM public.games
  WHERE slug = 'heart-of-crown';

  SELECT id INTO canonical_game_id
  FROM public.games
  WHERE slug = 'heart-of-crown-2nd-edition';

  IF generic_game_id IS NULL THEN
    RAISE EXCEPTION 'heart-of-crown row is missing';
  END IF;

  IF canonical_game_id IS NULL THEN
    RAISE EXCEPTION 'heart-of-crown-2nd-edition row is missing';
  END IF;

  SELECT count(*) INTO generic_ruleset_count
  FROM public.rule_sets
  WHERE game_id = generic_game_id;

  IF generic_ruleset_count <> 0 THEN
    RAISE EXCEPTION 'heart-of-crown unexpectedly has % RuleSets; inspect before retiring duplicate data', generic_ruleset_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = canonical_game_id
      AND identity_status = 'verified'
      AND content_review_status = 'review_required'
      AND source_url = 'https://games.flipflops.jp/heartofcrown'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
      AND min_players IS NULL
      AND max_players IS NULL
      AND play_time IS NULL
      AND play_time_min_minutes IS NULL
      AND play_time_max_minutes IS NULL
      AND min_age IS NULL
      AND published_year IS NULL
      AND rules = '{}'::jsonb
      AND rules_content IS NULL
  ) THEN
    RAISE EXCEPTION 'canonical Heart of Crown 2nd Edition is not in the expected fail-closed state';
  END IF;
END $$;

UPDATE public.games
SET
  title = 'Heart of Crown',
  title_ja = 'ハートオブクラウン',
  title_en = 'Heart of Crown',
  edition_label = NULL,
  language_code = NULL,
  publisher = NULL,
  is_official = false,
  identity_status = 'unverified',
  identity_source = NULL,
  source_trust = 'unknown',
  content_review_status = 'review_required',
  source_revision = 'ambiguous duplicate retired; exact physical edition and primary rules not source-bound; audited 2026-08-29',
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
WHERE slug = 'heart-of-crown';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE slug = 'heart-of-crown'
      AND title = 'Heart of Crown'
      AND title_ja = 'ハートオブクラウン'
      AND title_en = 'Heart of Crown'
      AND edition_label IS NULL
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
    RAISE EXCEPTION 'heart-of-crown duplicate did not reach fail-closed state';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE slug = 'heart-of-crown-2nd-edition'
      AND identity_status = 'verified'
      AND content_review_status = 'review_required'
      AND source_url = 'https://games.flipflops.jp/heartofcrown'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'canonical Heart of Crown 2nd Edition changed unexpectedly';
  END IF;
END $$;

COMMIT;
