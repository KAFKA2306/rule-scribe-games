BEGIN;

DO $$
DECLARE
  v_game_id uuid;
  v_source_url text;
BEGIN
  SELECT id, source_url
    INTO v_game_id, v_source_url
  FROM public.games
  WHERE slug = 'ito'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical game ito is required';
  END IF;

  IF v_source_url IS DISTINCT FROM 'https://arclightgames.jp/product/ito/' THEN
    RAISE EXCEPTION 'ito source_url drifted: %', v_source_url;
  END IF;

  UPDATE public.games
  SET max_players = 10,
      published_year = 2019,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND min_players = 2
      AND max_players = 10
      AND play_time = 30
      AND min_age = 8
      AND published_year = 2019
  ) THEN
    RAISE EXCEPTION 'ito metadata does not match official product facts after correction';
  END IF;
END $$;

COMMIT;
