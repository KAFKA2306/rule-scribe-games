BEGIN;

-- プレイヤー向け成功条件:
-- 「マグノリア」2021年3月11日日本語版が、アークライト公式の商品ページとFAQだけを根拠として検索公開され、
-- 2～5人・10～20分・10歳以上と表示されること。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'magnolia'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Magnolia canonical game row is not part of the source-bound fixture; skipping review migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Magnolia game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'マグノリア（2021年3月11日）'
    AND platform = 'physical'
    AND revision_label = 'arclight-2021-ja-product-faq'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY[
      'publisher:arclight:magnolia:2021-product',
      'publisher:arclight:magnolia:2021-faq'
    ]::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Magnolia Japanese 2021 RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 11 THEN
    RAISE EXCEPTION 'Magnolia requires exactly 11 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 11 THEN
    RAISE EXCEPTION 'Magnolia requires exactly 11 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 11 THEN
    RAISE EXCEPTION 'Magnolia requires exactly 11 supporting EvidenceBindings, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id = 'publisher:arclight:magnolia:2021-product';
  IF v_count <> 10 THEN
    RAISE EXCEPTION 'Magnolia product page must support exactly 10 accepted rules, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id = 'publisher:arclight:magnolia:2021-faq';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Magnolia FAQ must support exactly 1 accepted rule, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id NOT IN (
      'publisher:arclight:magnolia:2021-product',
      'publisher:arclight:magnolia:2021-faq'
    );
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Magnolia contains evidence from an unexpected source';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:arclight:magnolia:2021-product'
    AND source_type = 'publisher_product_page'
    AND publisher_name = 'Arclight'
    AND platform = 'physical'
    AND language_code = 'ja'
    AND revision_label = '2021-03-11 Japanese edition'
    AND url = 'https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Arclight Magnolia product source is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:arclight:magnolia:2021-faq'
    AND source_type = 'publisher_faq'
    AND publisher_name = 'Arclight'
    AND platform = 'physical'
    AND language_code = 'ja'
    AND revision_label = '2021-03-26 FAQ'
    AND url = 'https://arclightgames.jp/%E3%80%90faq%E3%80%91%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Arclight Magnolia FAQ source is missing or changed';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 2,
      max_players = 5,
      play_time = 20,
      play_time_min_minutes = 10,
      play_time_max_minutes = 20,
      min_age = 10,
      published_year = 2021,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND edition_label = 'マグノリア（2021年3月11日）'
      AND language_code = 'ja'
      AND min_players = 2
      AND max_players = 5
      AND play_time = 20
      AND play_time_min_minutes = 10
      AND play_time_max_minutes = 20
      AND min_age = 10
      AND published_year = 2021
      AND identity_source = 'https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Magnolia post-update verification failed';
  END IF;
END $$;

COMMIT;
