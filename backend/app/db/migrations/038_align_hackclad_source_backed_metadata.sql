BEGIN;

-- Canonical scope: base HacKClaD physical game only.
-- Official publisher product metadata: 1-4 players, 90-120 minutes.
-- Keep CROSS FATE, DeltA and Portable Edition out of this record.
UPDATE public.games
SET
  play_time = NULL,
  play_time_min_minutes = 90,
  play_time_max_minutes = 120,
  content_review_status = 'human_reviewed',
  source_url = 'https://www.hackclad.jp/home',
  official_url = 'https://www.hackclad.jp/home',
  source_trust = 'official_publisher',
  identity_status = 'verified',
  identity_source = 'https://www.hackclad.jp/home',
  edition_label = '基本セット HacKClaD（通常版）',
  language_code = 'ja',
  publisher = 'SUSABI GAMES',
  source_revision = 'Official website + base-rules FAQ; metadata re-audited 2026-08-27',
  updated_at = now()
WHERE slug = 'hack-clad'
  AND title = 'HacKClaD'
  AND work_id IS NOT NULL;

DO $$
DECLARE
  v_count integer;
BEGIN
  SELECT count(*) INTO v_count
  FROM public.games
  WHERE slug = 'hack-clad'
    AND title = 'HacKClaD'
    AND identity_status = 'verified'
    AND identity_source = 'https://www.hackclad.jp/home'
    AND source_url = 'https://www.hackclad.jp/home'
    AND source_trust = 'official_publisher'
    AND edition_label = '基本セット HacKClaD（通常版）'
    AND min_players = 1
    AND max_players = 4
    AND play_time IS NULL
    AND play_time_min_minutes = 90
    AND play_time_max_minutes = 120
    AND content_review_status = 'human_reviewed';

  IF v_count <> 1 THEN
    RAISE EXCEPTION 'HacKClaD source-backed metadata contract failed: expected 1 canonical row, found %', v_count;
  END IF;
END $$;

COMMIT;
