BEGIN;

-- Player-facing success condition:
-- /games/game must no longer expose a row that mixes two different products.
-- The canonical product rows remain separate and future catalog writes cannot
-- recreate the generic slug "game".
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_count integer;
  v_user_games_count integer;
  v_user_list_items_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'game';

  IF v_game_id IS NULL THEN
    IF current_database() = 'source_bound_ruleset_test' THEN
      RAISE NOTICE 'generic game slug is not part of the fixture; continuing with slug constraint';
    ELSE
      RAISE EXCEPTION 'generic game slug is missing; inspect production state before applying this migration';
    END IF;
  ELSE
    IF NOT EXISTS (
      SELECT 1 FROM public.games
      WHERE slug = 'raise-your-goblets'
        AND title = 'ワインと毒とゴブレット'
        AND identity_status = 'verified'
    ) THEN
      RAISE EXCEPTION 'canonical raise-your-goblets row is missing or unverified';
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM public.games
      WHERE slug = 'minna-de-ponkotsu-paint'
        AND title = 'みんなでぽんこつペイント'
        AND identity_status = 'verified'
    ) THEN
      RAISE EXCEPTION 'canonical minna-de-ponkotsu-paint row is missing or unverified';
    END IF;

    SELECT count(*) INTO v_ruleset_count FROM public.rule_sets WHERE game_id = v_game_id;
    SELECT count(*) INTO v_user_games_count FROM public.user_games WHERE game_id = v_game_id;
    SELECT count(*) INTO v_user_list_items_count FROM public.user_list_items WHERE game_id = v_game_id;

    IF v_ruleset_count <> 0 OR v_user_games_count <> 0 OR v_user_list_items_count <> 0 THEN
      RAISE EXCEPTION 'generic game row has dependent user/rules data: rule_sets %, user_games %, user_list_items %',
        v_ruleset_count, v_user_games_count, v_user_list_items_count;
    END IF;

    -- This row is not safe to merge. Its title/description identify
    -- ワインと毒とゴブレット while its summary/title aliases identify
    -- みんなでぽんこつペイント, so its 31 historical views cannot be
    -- attributed to either canonical product without inventing evidence.
    DELETE FROM public.game_generation_freshness WHERE game_id = v_game_id;
    DELETE FROM public.game_title_aliases WHERE game_id = v_game_id;
    DELETE FROM public.game_slug_aliases WHERE game_id = v_game_id;
    DELETE FROM public.game_concepts WHERE game_id = v_game_id;
    DELETE FROM public.games WHERE id = v_game_id;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'games_slug_not_generic_game'
      AND conrelid = 'public.games'::regclass
  ) THEN
    ALTER TABLE public.games
      ADD CONSTRAINT games_slug_not_generic_game
      CHECK (lower(slug) <> 'game') NOT VALID;
  END IF;
END $$;

ALTER TABLE public.games VALIDATE CONSTRAINT games_slug_not_generic_game;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.games WHERE lower(slug) = 'game') THEN
    RAISE EXCEPTION 'generic game slug still exists after cleanup';
  END IF;
END $$;

COMMIT;
