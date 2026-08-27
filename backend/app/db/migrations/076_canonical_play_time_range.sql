BEGIN;

ALTER TABLE public.games
  ADD COLUMN IF NOT EXISTS play_time_min_minutes integer,
  ADD COLUMN IF NOT EXISTS play_time_max_minutes integer;

UPDATE public.games
SET play_time_min_minutes = play_time,
    play_time_max_minutes = play_time
WHERE play_time IS NOT NULL
  AND play_time > 0
  AND play_time_min_minutes IS NULL
  AND play_time_max_minutes IS NULL;

DO $$
DECLARE
  v_source_url text;
  v_source_trust text;
BEGIN
  SELECT source_url, source_trust
    INTO v_source_url, v_source_trust
  FROM public.games
  WHERE slug = 'skull-king'
  LIMIT 1;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Canonical game skull-king is required';
  END IF;

  IF v_source_url IS DISTINCT FROM 'https://www.grandpabecksgames.com/pages/skull-king' THEN
    RAISE EXCEPTION 'skull-king source_url drifted: %', v_source_url;
  END IF;

  IF v_source_trust IS DISTINCT FROM 'official_publisher' THEN
    RAISE EXCEPTION 'skull-king source_trust drifted: %', v_source_trust;
  END IF;

  UPDATE public.games
  SET play_time_min_minutes = 30,
      play_time_max_minutes = 45,
      updated_at = now()
  WHERE slug = 'skull-king';
END $$;

ALTER TABLE public.games
  DROP CONSTRAINT IF EXISTS games_play_time_range_valid;

ALTER TABLE public.games
  ADD CONSTRAINT games_play_time_range_valid CHECK (
    (play_time_min_minutes IS NULL AND play_time_max_minutes IS NULL)
    OR (
      play_time_min_minutes IS NOT NULL
      AND play_time_max_minutes IS NOT NULL
      AND play_time_min_minutes > 0
      AND play_time_max_minutes >= play_time_min_minutes
    )
  );

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE slug = 'skull-king'
      AND play_time_min_minutes = 30
      AND play_time_max_minutes = 45
      AND play_time IS NULL
  ) THEN
    RAISE EXCEPTION 'skull-king canonical duration must be 30-45 minutes without a fabricated scalar';
  END IF;
END $$;

COMMIT;
