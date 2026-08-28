BEGIN;

-- プレイヤー向け成功条件:
-- Forest Shuffle基本ゲームの公開根拠が英語のLookout Games公式資料として正しく記録され、
-- 公式商品情報の10歳以上・2023年発売・公式URLがcanonical game rowへ反映されること。
-- 現在の6ルールではセットアップと「カードを2枚引く」手番選択を十分に説明できないため、検索公開には昇格させない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'forest-shuffle'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Forest Shuffle canonical game row is not part of the source-bound fixture; skipping metadata correction';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Forest Shuffle game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND title = 'Forest Shuffle'
      AND edition_label = 'Lookout Forest Shuffle base game 2023 / current official rules'
      AND language_code = 'ja'
      AND min_players = 2
      AND max_players = 5
      AND play_time = 60
      AND play_time_min_minutes = 60
      AND play_time_max_minutes = 60
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'review_required'
      AND identity_source = 'https://www.lookout-spiele.de/en/games/forrestshuffle.html'
  ) THEN
    RAISE EXCEPTION 'Canonical Forest Shuffle identity or review state is missing or changed';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'Lookout Forest Shuffle base game 2023 / current official rules'
    AND platform = 'physical'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY[
      'forest-shuffle:lookout-product',
      'forest-shuffle:lookout-rulebook'
    ]::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Forest Shuffle base RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 6 THEN
    RAISE EXCEPTION 'Forest Shuffle currently requires exactly 6 source-bound RuleNodes before this correction, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 6 THEN
    RAISE EXCEPTION 'Forest Shuffle currently requires exactly 6 accepted Claims before this correction, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 6 THEN
    RAISE EXCEPTION 'Forest Shuffle currently requires exactly 6 supporting EvidenceBindings before this correction, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'forest-shuffle:lookout-rulebook';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Forest Shuffle base rules contain support outside the official Lookout rulebook';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'forest-shuffle:lookout-product'
      AND source_type = 'publisher_product_page'
      AND platform = 'physical'
      AND url = 'https://www.lookout-spiele.de/en/games/forrestshuffle.html'
  ) THEN
    RAISE EXCEPTION 'Expected Lookout Forest Shuffle product source is missing or changed';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'forest-shuffle:lookout-rulebook'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND url = 'https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf'
  ) THEN
    RAISE EXCEPTION 'Expected Lookout Forest Shuffle rulebook source is missing or changed';
  END IF;

  UPDATE public.evidence_sources
  SET language_code = 'en',
      updated_at = now()
  WHERE source_id IN (
    'forest-shuffle:lookout-product',
    'forest-shuffle:lookout-rulebook'
  );

  UPDATE public.games
  SET min_age = 10,
      published_year = 2023,
      official_url = 'https://www.lookout-spiele.de/en/games/forrestshuffle.html',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'forest-shuffle:lookout-product'
      AND language_code = 'en'
      AND url = 'https://www.lookout-spiele.de/en/games/forrestshuffle.html'
  ) OR NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'forest-shuffle:lookout-rulebook'
      AND language_code = 'en'
      AND url = 'https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf'
  ) THEN
    RAISE EXCEPTION 'Forest Shuffle official source language correction failed';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND min_players = 2
      AND max_players = 5
      AND play_time = 60
      AND play_time_min_minutes = 60
      AND play_time_max_minutes = 60
      AND min_age = 10
      AND published_year = 2023
      AND official_url = 'https://www.lookout-spiele.de/en/games/forrestshuffle.html'
      AND content_review_status = 'review_required'
  ) THEN
    RAISE EXCEPTION 'Forest Shuffle canonical metadata correction or review boundary failed';
  END IF;
END $$;

COMMIT;
