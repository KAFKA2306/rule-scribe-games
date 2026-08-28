BEGIN;

-- プレイヤー向け完了条件:
-- エバーデール 完全日本語版（2020年1月9日）の基本ゲーム11ルールが、
-- Starling Games公式基本ルールブックまたはアークライト公式FAQにすべて結び付き、
-- 拡張ルールを混ぜず、公式商品情報の1～4人・40～80分・10歳以上を保持できる場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'everdell'
  LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Everdell Japanese base game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'エバーデール 完全日本語版（2020年1月9日）'
    AND COALESCE(revision_label, '') = 'arclight-2020-ja-starling-core'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;
  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Everdell Japanese 2020 RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 11 THEN
    RAISE EXCEPTION 'Everdell requires exactly 11 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 11 THEN
    RAISE EXCEPTION 'Everdell requires exactly 11 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
  ) <> 11 THEN
    RAISE EXCEPTION 'Everdell requires exactly 11 supporting evidence bindings';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
      AND eb.source_id NOT IN (
        'publisher:starling:everdell:core-rulebook-en',
        'publisher:arclight:everdell:faq-ja'
      )
  ) THEN
    RAISE EXCEPTION 'Everdell expansion or unrelated evidence must not be mixed into the base rules';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:arclight:everdell:2020-ja'
      AND publisher_name = 'アークライト'
      AND url = 'https://arclightgames.jp/product/%E3%82%A8%E3%83%90%E3%83%BC%E3%83%87%E3%83%BC%E3%83%AB/'
      AND revision_label = 'japanese-release-2020-01-09'
  ) THEN
    RAISE EXCEPTION 'Official Arclight Everdell Japanese 2020 product source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:starling:everdell:core-rulebook-en'
      AND publisher_name = 'Starling Games'
      AND source_type = 'publisher_rulebook'
      AND revision_label = 'core-rulebook-current'
  ) THEN
    RAISE EXCEPTION 'Official Starling Games Everdell core rulebook source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:arclight:everdell:faq-ja'
      AND publisher_name = 'アークライト'
      AND source_type = 'publisher_faq'
      AND revision_label = 'faq-2022-06-29'
  ) THEN
    RAISE EXCEPTION 'Official Arclight Everdell FAQ source is required';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 1,
      max_players = 4,
      play_time = 80,
      play_time_min_minutes = 40,
      play_time_max_minutes = 80,
      min_age = 10,
      published_year = 2020,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND min_players = 1
      AND max_players = 4
      AND play_time = 80
      AND play_time_min_minutes = 40
      AND play_time_max_minutes = 80
      AND min_age = 10
      AND published_year = 2020
  ) THEN
    RAISE EXCEPTION 'Everdell review or official product metadata update failed';
  END IF;
END $$;

COMMIT;
