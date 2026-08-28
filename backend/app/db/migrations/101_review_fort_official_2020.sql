BEGIN;

-- プレイヤー向け成功条件:
-- Leder Games の Fort 基本版が、Leder Games 公式商品ページと公式ルールブックだけを根拠として検索公開され、
-- 2～4人・20～40分・10歳以上と表示されること。拡張や非公式FAQは混ぜない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'fort'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Fort canonical game row is not part of the source-bound fixture; skipping review migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Fort game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'Leder Games Fort core game rulebook 2020-10-15'
    AND platform = 'physical'
    AND revision_label = 'leder-fort-rulebook-2020-10-15-accessed-2026-08-26'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY['fort:leder-product','fort:leder-rulebook-2020-10-15']::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Fort core-game RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 7 THEN
    RAISE EXCEPTION 'Fort requires exactly 7 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 7 THEN
    RAISE EXCEPTION 'Fort requires exactly 7 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 7 THEN
    RAISE EXCEPTION 'Fort requires exactly 7 supporting EvidenceBindings, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'fort:leder-rulebook-2020-10-15';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Fort contains supporting rule evidence from an unexpected source';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'fort:leder-product'
    AND source_type = 'publisher_product_page'
    AND platform = 'physical'
    AND url = 'https://ledergames.com/products/fort';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Leder Games Fort product source is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'fort:leder-rulebook-2020-10-15'
    AND source_type = 'publisher_rulebook'
    AND platform = 'physical'
    AND revision_label = '2020-10-15'
    AND url = 'https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Leder Games Fort rulebook source is missing or changed';
  END IF;

  -- 公式資料は英語。既存の日本語表示用 RuleSet と evidence source の言語を混同しない。
  UPDATE public.evidence_sources
  SET language_code = 'en', updated_at = now()
  WHERE source_id IN ('fort:leder-product','fort:leder-rulebook-2020-10-15');

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 2,
      max_players = 4,
      play_time = 40,
      play_time_min_minutes = 20,
      play_time_max_minutes = 40,
      min_age = 10,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND edition_label = 'Leder Games Fort core game rulebook 2020-10-15'
      AND language_code = 'ja'
      AND min_players = 2
      AND max_players = 4
      AND play_time = 40
      AND play_time_min_minutes = 20
      AND play_time_max_minutes = 40
      AND min_age = 10
      AND identity_source = 'https://ledergames.com/products/fort'
      AND source_url = 'https://ledergames.com/products/fort'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Fort post-update verification failed';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id IN ('fort:leder-product','fort:leder-rulebook-2020-10-15')
      AND language_code <> 'en'
  ) THEN
    RAISE EXCEPTION 'Fort official source language must remain English';
  END IF;
END $$;

COMMIT;
