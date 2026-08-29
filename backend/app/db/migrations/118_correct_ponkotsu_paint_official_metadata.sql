BEGIN;

-- プレイヤー向け成功条件:
-- 「みんなでぽんこつペイント」の商品情報をホビージャパン公式ページに一致させ、
-- 一次資料で裏付けられない旧ルール本文は、確認済みRuleSetができるまで公開しない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'minna-de-ponkotsu-paint'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Minna de Ponkotsu Paint canonical game row is not part of the fixture; skipping';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Minna de Ponkotsu Paint game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND title = 'みんなでぽんこつペイント'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND source_url = 'https://hobbyjapan.games/ponkotsu_paint/'
      AND min_players = 3
      AND max_players = 12
      AND play_time = 10
      AND play_time_min_minutes = 10
      AND play_time_max_minutes = 10
      AND min_age = 6
      AND published_year = 2020
      AND rules_content IS NOT NULL
      AND btrim(rules_content) <> ''
  ) THEN
    RAISE EXCEPTION 'Minna de Ponkotsu Paint canonical state changed; re-audit before migration';
  END IF;

  SELECT count(*) INTO v_ruleset_count
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active';

  IF v_ruleset_count <> 0 THEN
    RAISE EXCEPTION 'Minna de Ponkotsu Paint now has an active RuleSet; migrate from that authority instead';
  END IF;

  UPDATE public.games
  SET min_players = 2,
      max_players = 12,
      play_time = 10,
      play_time_min_minutes = 10,
      play_time_max_minutes = 10,
      min_age = 6,
      published_year = 2018,
      rules_content = NULL,
      content_review_status = 'review_required',
      summary = 'サイコロで決めたお題を「直線」と「正円」だけで描き、画数が少ない絵から回答者に見せるお絵かきゲームです。',
      description = 'ホビージャパンの2018年新装版。2～12人、約10分、6歳以上。基本のお絵かきに加え、7人までの「ぽんこつ紅白チーム戦」と2人用協力戦「ぽんこつデュエット」が収録されています。詳細ルールは一次資料との照合が完了するまで掲載しません。',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND source_url = 'https://hobbyjapan.games/ponkotsu_paint/'
      AND min_players = 2
      AND max_players = 12
      AND play_time = 10
      AND play_time_min_minutes = 10
      AND play_time_max_minutes = 10
      AND min_age = 6
      AND published_year = 2018
      AND rules_content IS NULL
      AND content_review_status = 'review_required'
      AND summary = 'サイコロで決めたお題を「直線」と「正円」だけで描き、画数が少ない絵から回答者に見せるお絵かきゲームです。'
  ) THEN
    RAISE EXCEPTION 'Minna de Ponkotsu Paint correction did not reach the required official state';
  END IF;
END $$;

COMMIT;
