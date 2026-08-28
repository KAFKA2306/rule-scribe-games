BEGIN;

-- プレイヤー向け成功条件:
-- 「藪の中 旧版（2010年）」の RuleSet が2010年旧版のオインクゲームズ公式商品ページだけを根拠として保持され、
-- 2021年新版の source が旧版 RuleSet に混ざらないこと。
-- 現在の5ルールだけでは旧版の得点・ゲーム終了まで十分に説明できないため、検索公開には昇格させない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'in-a-grove'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'In a Grove canonical game row is not part of the source-bound fixture; skipping source-boundary migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical In a Grove game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND title_ja = '藪の中'
      AND edition_label = '藪の中 旧版（2010年）'
      AND language_code = 'ja'
      AND publisher = 'オインクゲームズ'
      AND published_year = 2010
      AND min_players = 3
      AND max_players = 4
      AND play_time = 20
      AND play_time_min_minutes = 20
      AND play_time_max_minutes = 20
      AND min_age = 9
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'review_required'
      AND official_url = 'https://oinkgames.com/ja/games/analog/in-a-grove/'
  ) THEN
    RAISE EXCEPTION 'Canonical In a Grove 2010 identity or review state is missing or changed';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = '藪の中 旧版（2010年）'
    AND platform = 'physical'
    AND publisher_name = 'オインクゲームズ'
    AND revision_label = 'oink-original-2010'
    AND verification_status = 'source_bound'
    AND 'publisher:oink:in-a-grove:2010-ja' = ANY(source_ids)
    AND source_ids <@ ARRAY[
      'publisher:oink:in-a-grove:2010-ja',
      'publisher:oink:in-a-grove:2021-revised-ja'
    ]::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound In a Grove 2010 RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 5 THEN
    RAISE EXCEPTION 'In a Grove 2010 requires exactly 5 current source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 5 THEN
    RAISE EXCEPTION 'In a Grove 2010 requires exactly 5 current accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 5 THEN
    RAISE EXCEPTION 'In a Grove 2010 requires exactly 5 current supporting EvidenceBindings, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'publisher:oink:in-a-grove:2010-ja';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'In a Grove 2010 contains supporting rule evidence from another edition';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:oink:in-a-grove:2010-ja'
    AND source_type = 'publisher_product_page'
    AND publisher_name = 'オインクゲームズ'
    AND platform = 'physical'
    AND language_code = 'ja'
    AND revision_label = 'original-2010'
    AND url = 'https://oinkgames.com/ja/games/analog/in-a-grove/';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Oink Games In a Grove 2010 source is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:oink:in-a-grove:2021-revised-ja'
    AND source_type = 'publisher_product_page'
    AND publisher_name = 'オインクゲームズ'
    AND platform = 'physical'
    AND language_code = 'ja'
    AND revision_label = 'revised-2021'
    AND url = 'https://oinkgames.com/ja/games/analog/in-a-grove-new/';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Oink Games In a Grove 2021 revised-edition source is missing or changed';
  END IF;

  UPDATE public.rule_sets
  SET source_ids = ARRAY['publisher:oink:in-a-grove:2010-ja']::text[],
      updated_at = now()
  WHERE id = v_ruleset_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.rule_sets
    WHERE id = v_ruleset_id
      AND source_ids = ARRAY['publisher:oink:in-a-grove:2010-ja']::text[]
      AND edition_label = '藪の中 旧版（2010年）'
      AND revision_label = 'oink-original-2010'
      AND verification_status = 'source_bound'
      AND is_active = true
  ) THEN
    RAISE EXCEPTION 'In a Grove 2010 source boundary post-update verification failed';
  END IF;

  -- 5件では旧版の得点・終了条件まで十分に説明できない。公開状態を勝手に昇格させない。
  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'review_required'
  ) THEN
    RAISE EXCEPTION 'In a Grove 2010 must remain review_required until rule coverage is sufficient';
  END IF;
END $$;

COMMIT;
