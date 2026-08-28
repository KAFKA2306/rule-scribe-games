BEGIN;

-- プレイヤー向け成功条件:
-- アークライト「タイムボム」2017年リニューアル版のプレイ時間を、
-- 現行公式商品ページの「1～30分」と一致させる。
-- 詳細ルールは公式説明書を直接検証できていないため、検索公開には昇格させない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'time-bomb'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Time Bomb canonical game row is not part of the source-bound fixture; skipping play-time correction';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Time Bomb game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND title = 'Time Bomb'
      AND edition_label = 'アークライト リニューアル版（2017）'
      AND language_code = 'ja'
      AND min_players = 2
      AND max_players = 8
      AND min_age = 10
      AND published_year = 2017
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'review_required'
      AND official_url = 'https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/'
  ) THEN
    RAISE EXCEPTION 'Canonical Time Bomb 2017 identity or review state is missing or changed';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'アークライト リニューアル版（2017）'
    AND platform = 'physical'
    AND revision_label = 'arclight-2017-core'
    AND verification_status = 'source_bound'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Time Bomb 2017 RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 2 THEN
    RAISE EXCEPTION 'Time Bomb currently requires exactly 2 source-bound RuleNodes before this correction, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND target_type = 'rule_node'
    AND lifecycle_status = 'accepted';
  IF v_count <> 2 THEN
    RAISE EXCEPTION 'Time Bomb currently requires exactly 2 accepted rule Claims before this correction, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.target_type = 'rule_node'
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 2 THEN
    RAISE EXCEPTION 'Time Bomb currently requires exactly 2 supporting rule EvidenceBindings before this correction, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:arclight:time-bomb:2017-product'
      AND source_type = 'publisher_product'
      AND publisher_name = 'アークライト'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND url = 'https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/'
  ) THEN
    RAISE EXCEPTION 'Expected Arclight Time Bomb 2017 product source is missing or changed';
  END IF;

  UPDATE public.games
  SET play_time = NULL,
      play_time_min_minutes = 1,
      play_time_max_minutes = 30,
      source_revision = 'Arclight official 2017-11-24 product identity; 1-30 minute official play-time range; detailed rulebook not directly verified; audited 2026-08-29',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Arclight official 2017-11-24 product identity; 1-30 minute official play-time range; detailed rulebook not directly verified; audited 2026-08-29',
      updated_at = now()
  WHERE id = v_ruleset_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND min_players = 2
      AND max_players = 8
      AND play_time IS NULL
      AND play_time_min_minutes = 1
      AND play_time_max_minutes = 30
      AND min_age = 10
      AND published_year = 2017
      AND content_review_status = 'review_required'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Time Bomb canonical play-time correction or review boundary failed';
  END IF;
END $$;

COMMIT;
