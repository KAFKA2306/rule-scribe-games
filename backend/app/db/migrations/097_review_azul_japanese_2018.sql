BEGIN;

-- プレイヤー向け成功条件:
-- アズール日本語版（2018年2月）が、基本ゲームの公式ルール13件だけを根拠として検索公開され、
-- 2～4人・30～45分・8歳以上と表示されること。
-- アズール ミニ、クリスタルモザイク、マスターショコラティエ、デュエル、
-- シントラのステンドグラス、サマーパビリオン等はこのRuleSetに含めない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'azul'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Azul canonical game row is not part of the source-bound fixture; skipping review migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Azul game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'アズール 日本語版（2018年2月）'
    AND platform = 'physical'
    AND revision_label = 'plan-b-base-rulebook-2017'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY[
      'publisher:hobbyjapan:azul:product-ja',
      'publisher:planb:azul:rules-en-2017'
    ]::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Azul Japanese 2018 base RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 13 THEN
    RAISE EXCEPTION 'Azul requires exactly 13 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 13 THEN
    RAISE EXCEPTION 'Azul requires exactly 13 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 13 THEN
    RAISE EXCEPTION 'Azul requires exactly 13 supporting EvidenceBindings, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'publisher:planb:azul:rules-en-2017';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Azul base rules contain evidence from an unexpected source';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:planb:azul:rules-en-2017'
    AND publisher_name = 'Plan B Games Inc.'
    AND source_type = 'publisher_rulebook'
    AND platform = 'physical'
    AND language_code = 'en'
    AND revision_label = 'copyright-2017'
    AND url = 'https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Plan B Games Azul 2017 rulebook source is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'publisher:hobbyjapan:azul:product-ja'
    AND publisher_name = 'ホビージャパン'
    AND source_type = 'publisher_product_page'
    AND platform = 'physical'
    AND language_code = 'ja'
    AND url = 'https://hobbyjapan.games/azul/';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Hobby Japan Azul Japanese product source is missing or changed';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 2,
      max_players = 4,
      play_time = 45,
      play_time_min_minutes = 30,
      play_time_max_minutes = 45,
      min_age = 8,
      published_year = 2018,
      publisher = 'Next Move Games',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND edition_label = 'アズール 日本語版（2018年2月）'
      AND language_code = 'ja'
      AND min_players = 2
      AND max_players = 4
      AND play_time = 45
      AND play_time_min_minutes = 30
      AND play_time_max_minutes = 45
      AND min_age = 8
      AND published_year = 2018
      AND publisher = 'Next Move Games'
      AND identity_source = 'https://hobbyjapan.games/azul/'
  ) THEN
    RAISE EXCEPTION 'Azul post-update verification failed';
  END IF;
END $$;

COMMIT;
