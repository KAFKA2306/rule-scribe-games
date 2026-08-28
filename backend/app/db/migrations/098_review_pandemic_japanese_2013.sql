BEGIN;

-- プレイヤー向け成功条件:
-- 「パンデミック：新たなる試練」日本語版（2013年7月）が、Z-MAN Games公式の基本ゲームルール12件だけを根拠として検索公開され、
-- 2～4人・約45分・8歳以上と表示されること。
-- 旧日本語版、拡張、Legacy、Hot Zone、Rapid Response、The Cure、Reign of Cthulhu等はこのRuleSetに含めない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'pandemic'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Pandemic game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'パンデミック：新たなる試練 日本語版（2013年7月）'
    AND platform = 'physical'
    AND revision_label = 'zman-base-rulebook-current'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY[
      'publisher:hobbyjapan:pandemic:new-ja',
      'publisher:zman:pandemic:rulebook-en'
    ]::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Pandemic Japanese 2013 base RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 12 THEN
    RAISE EXCEPTION 'Pandemic requires exactly 12 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 12 THEN
    RAISE EXCEPTION 'Pandemic requires exactly 12 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 12 THEN
    RAISE EXCEPTION 'Pandemic requires exactly 12 supporting EvidenceBindings, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'publisher:zman:pandemic:rulebook-en';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Pandemic base rules contain evidence from an unexpected source';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:zman:pandemic:rulebook-en'
    AND publisher_name = 'Z-MAN Games'
    AND source_type = 'publisher_rulebook'
    AND platform = 'physical'
    AND language_code = 'en'
    AND revision_label = 'current-official-rulebook'
    AND url = 'https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Z-MAN Games Pandemic base rulebook source is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:hobbyjapan:pandemic:new-ja'
    AND publisher_name = 'ホビージャパン'
    AND source_type = 'publisher_product_page'
    AND platform = 'physical'
    AND language_code = 'ja'
    AND revision_label = 'japanese-release-2013-07'
    AND url = 'https://hobbyjapan.games/pandemic_new/';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Hobby Japan Pandemic Japanese product source is missing or changed';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 2,
      max_players = 4,
      play_time = 45,
      play_time_min_minutes = 45,
      play_time_max_minutes = 45,
      min_age = 8,
      published_year = 2013,
      publisher = 'Z-MAN Games',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND edition_label = 'パンデミック：新たなる試練 日本語版（2013年7月）'
      AND language_code = 'ja'
      AND min_players = 2
      AND max_players = 4
      AND play_time = 45
      AND play_time_min_minutes = 45
      AND play_time_max_minutes = 45
      AND min_age = 8
      AND published_year = 2013
      AND publisher = 'Z-MAN Games'
      AND identity_source = 'https://hobbyjapan.games/pandemic_new/'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Pandemic post-update verification failed';
  END IF;
END $$;

COMMIT;
