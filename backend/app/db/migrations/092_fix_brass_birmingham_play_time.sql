BEGIN;

-- プレイヤー向け完了条件:
-- ブラス：バーミンガム 完全日本語版の公式プレイ時間「60～120分」を、
-- 本番データと公開ページで単一値120分へ潰さず保持する。
DO $$
DECLARE
  v_game_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'brass-birmingham'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Brass: Birmingham game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'localizer:arclight:brass-birmingham:product'
      AND publisher_name = 'アークライト'
  ) THEN
    RAISE EXCEPTION 'Official Arclight Brass: Birmingham product source is required';
  END IF;

  IF (
    SELECT content_review_status
    FROM public.games
    WHERE id = v_game_id
  ) <> 'human_reviewed' THEN
    RAISE EXCEPTION 'Brass: Birmingham must remain human reviewed before metadata correction';
  END IF;

  UPDATE public.games
  SET play_time = 120,
      play_time_min_minutes = 60,
      play_time_max_minutes = 120,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND play_time = 120
      AND play_time_min_minutes = 60
      AND play_time_max_minutes = 120
  ) THEN
    RAISE EXCEPTION 'Brass: Birmingham official 60-120 minute range was not preserved';
  END IF;
END $$;

COMMIT;
