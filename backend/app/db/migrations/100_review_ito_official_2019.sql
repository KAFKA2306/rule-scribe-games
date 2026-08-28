BEGIN;

-- プレイヤー向け成功条件:
-- 「ito」2019年8月8日発売の基本版が、アークライト公式の商品・ルールページだけを根拠として検索公開され、
-- 2～10人・約30分・8歳以上と表示されること。ito レインボー、ito クラシック等は混ぜない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'ito'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'ito canonical game row is not part of the source-bound fixture; skipping review migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical ito game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'アークライト ito 基本版（2019年8月8日）'
    AND platform = 'physical'
    AND revision_label = 'arclight-ito-base-2019-accessed-2026-08-26'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY['ito:arclight-rules-page']::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound ito Japanese 2019 RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'ito requires exactly 9 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 12 THEN
    RAISE EXCEPTION 'ito requires exactly 12 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 12 THEN
    RAISE EXCEPTION 'ito requires exactly 12 supporting EvidenceBindings, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'ito:arclight-rules-page';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'ito contains supporting evidence from an unexpected source';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'ito:arclight-rules-page'
    AND source_type = 'publisher_rules_page'
    AND platform = 'physical'
    AND language_code = 'ja'
    AND revision_label = 'current official base-product rules page accessed 2026-08-26'
    AND url = 'https://arclightgames.jp/product/ito/';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Arclight ito official source is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted'
    AND target_type = 'game_metadata'
    AND field_path IN ('min_players', 'max_players', 'play_time');
  IF v_count <> 3 THEN
    RAISE EXCEPTION 'ito requires exactly 3 accepted metadata Claims, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND claim_id = 'ito:metadata:min_players'
      AND lifecycle_status = 'accepted'
      AND normalized_payload ->> 'value' = '2'
  ) OR NOT EXISTS (
    SELECT 1 FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND claim_id = 'ito:metadata:max_players'
      AND lifecycle_status = 'accepted'
      AND normalized_payload ->> 'value' = '10'
  ) OR NOT EXISTS (
    SELECT 1 FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND claim_id = 'ito:metadata:play_time'
      AND lifecycle_status = 'accepted'
      AND normalized_payload ->> 'value' = '30'
  ) THEN
    RAISE EXCEPTION 'ito official metadata Claims are missing or changed';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 2,
      max_players = 10,
      play_time = 30,
      play_time_min_minutes = 30,
      play_time_max_minutes = 30,
      min_age = 8,
      published_year = 2019,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND edition_label = 'アークライト ito 基本版（2019年8月8日）'
      AND language_code = 'ja'
      AND min_players = 2
      AND max_players = 10
      AND play_time = 30
      AND play_time_min_minutes = 30
      AND play_time_max_minutes = 30
      AND min_age = 8
      AND published_year = 2019
      AND identity_source = 'https://arclightgames.jp/product/ito/'
      AND source_url = 'https://arclightgames.jp/product/ito/'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'ito post-update verification failed';
  END IF;
END $$;

COMMIT;
