BEGIN;

-- プレイヤー向け成功条件:
-- productionで identity_status='verified' と表示されるゲームは、
-- 後から確認できる identity_source を必ず持つこと。
-- publisher sourceが確認できない Relative Space は、既存のBoard Game Arena実装を
-- platform identityの根拠として明示し、publisher sourceとは扱わない。

DO $$
DECLARE
  v_missing integer;
BEGIN
  IF current_database() <> 'source_bound_ruleset_test' THEN
    IF NOT EXISTS (
      SELECT 1 FROM public.games
      WHERE slug = 'coup'
        AND identity_status = 'verified'
        AND identity_source IS NULL
        AND official_url = 'https://indieboardsandcards.com/our-games/coup/'
    ) THEN
      RAISE EXCEPTION 'coup identity state changed; re-audit before migration';
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM public.games
      WHERE slug = 'raise-your-goblets'
        AND identity_status = 'verified'
        AND identity_source IS NULL
        AND official_url = 'https://hobbyjapan.games/wine_poison_and_goblets/'
    ) THEN
      RAISE EXCEPTION 'raise-your-goblets identity state changed; re-audit before migration';
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM public.games
      WHERE slug = 'yro'
        AND identity_status = 'verified'
        AND identity_source IS NULL
        AND official_url = 'https://www.studiosupernova.it/products/yro'
    ) THEN
      RAISE EXCEPTION 'yro identity state changed; re-audit before migration';
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM public.games
      WHERE slug = 'relative-space'
        AND identity_status = 'verified'
        AND identity_source IS NULL
        AND official_url IS NULL
        AND source_url = 'https://en.boardgamearena.com/gamepanel?game=relativespace'
        AND source_trust = 'third_party'
    ) THEN
      RAISE EXCEPTION 'relative-space identity state changed; re-audit before migration';
    END IF;
  END IF;

  UPDATE public.games
  SET identity_source = 'https://indieboardsandcards.com/our-games/coup/',
      updated_at = now()
  WHERE slug = 'coup'
    AND identity_status = 'verified'
    AND identity_source IS NULL;

  UPDATE public.games
  SET identity_source = 'https://hobbyjapan.games/wine_poison_and_goblets/',
      updated_at = now()
  WHERE slug = 'raise-your-goblets'
    AND identity_status = 'verified'
    AND identity_source IS NULL;

  UPDATE public.games
  SET identity_source = 'https://www.studiosupernova.it/products/yro',
      updated_at = now()
  WHERE slug = 'yro'
    AND identity_status = 'verified'
    AND identity_source IS NULL;

  UPDATE public.games
  SET identity_source = 'https://en.boardgamearena.com/gamepanel?game=relativespace',
      updated_at = now()
  WHERE slug = 'relative-space'
    AND identity_status = 'verified'
    AND identity_source IS NULL;

  SELECT count(*) INTO v_missing
  FROM public.games
  WHERE identity_status = 'verified'
    AND nullif(btrim(identity_source), '') IS NULL;

  IF v_missing <> 0 THEN
    RAISE EXCEPTION 'verified games without identity_source remain: %', v_missing;
  END IF;
END $$;

ALTER TABLE public.games
  DROP CONSTRAINT IF EXISTS games_verified_identity_requires_source_check;

ALTER TABLE public.games
  ADD CONSTRAINT games_verified_identity_requires_source_check
  CHECK (
    identity_status <> 'verified'
    OR nullif(btrim(identity_source), '') IS NOT NULL
  );

DO $$
DECLARE
  v_count integer;
BEGIN
  SELECT count(*) INTO v_count
  FROM public.games
  WHERE identity_status = 'verified'
    AND nullif(btrim(identity_source), '') IS NULL;

  IF v_count <> 0 THEN
    RAISE EXCEPTION 'verified identity provenance contract failed: % rows', v_count;
  END IF;
END $$;

COMMIT;
