BEGIN;

-- プレイヤー向け成功条件:
-- ララチラゲームズ「ジャンブルダービー」2023秋版のプレイ時間を、
-- 作者公式のGame Market掲載とBOOTH商品ページの「45～90分」に一致させる。
-- 詳細な通常ルールは一次ルール本文を確認できていないため、検索公開には昇格させない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'jumble-derby'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Jumble Derby canonical game row is not part of the source-bound fixture; skipping play-time correction';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Jumble Derby game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND title = 'Jumble Derby'
      AND edition_label = 'ジャンブルダービー（2023秋版）'
      AND language_code = 'ja'
      AND min_players = 3
      AND max_players = 5
      AND min_age = 10
      AND published_year = 2023
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'review_required'
      AND identity_source = 'https://gamemarket.jp/game/181906'
      AND official_url = 'https://booth.pm/ja/items/5338090'
  ) THEN
    RAISE EXCEPTION 'Canonical Jumble Derby 2023 identity or review state is missing or changed';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'ジャンブルダービー（2023秋版）'
    AND platform = 'physical'
    AND revision_label = 'creator-core-2023-autumn'
    AND verification_status = 'source_bound'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Jumble Derby 2023 RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 3 THEN
    RAISE EXCEPTION 'Jumble Derby currently requires exactly 3 source-bound RuleNodes before this correction, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND target_type = 'rule_node'
    AND lifecycle_status = 'accepted';
  IF v_count <> 3 THEN
    RAISE EXCEPTION 'Jumble Derby currently requires exactly 3 accepted rule Claims before this correction, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.target_type = 'rule_node'
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 3 THEN
    RAISE EXCEPTION 'Jumble Derby currently requires exactly 3 supporting rule EvidenceBindings before this correction, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'creator:lalachira:jumble-derby:gamemarket'
      AND source_type = 'creator_listing'
      AND publisher_name = 'ララチラゲームズ'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND url = 'https://gamemarket.jp/game/181906'
  ) THEN
    RAISE EXCEPTION 'Expected creator Game Market source for Jumble Derby is missing or changed';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.source_locators
    WHERE locator_id = 'jumble-derby:gamemarket:identity'
      AND source_id = 'creator:lalachira:jumble-derby:gamemarket'
      AND external_reference LIKE '%45%90%'
  ) THEN
    RAISE EXCEPTION 'Jumble Derby official 45-90 minute identity locator is missing or changed';
  END IF;

  UPDATE public.games
  SET play_time = NULL,
      play_time_min_minutes = 45,
      play_time_max_minutes = 90,
      source_revision = 'Creator Game Market 2023秋 listing and current BOOTH storefront; official 45-90 minute play-time range; detailed normal rules remain unverified; audited 2026-08-29',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Creator Game Market 2023秋 listing and current BOOTH storefront; official 45-90 minute play-time range; detailed normal rules remain unverified; audited 2026-08-29',
      updated_at = now()
  WHERE id = v_ruleset_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND min_players = 3
      AND max_players = 5
      AND play_time IS NULL
      AND play_time_min_minutes = 45
      AND play_time_max_minutes = 90
      AND min_age = 10
      AND published_year = 2023
      AND content_review_status = 'review_required'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Jumble Derby canonical play-time correction or review boundary failed';
  END IF;
END $$;

COMMIT;
