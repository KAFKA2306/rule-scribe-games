BEGIN;

-- プレイヤー向け成功条件:
-- human_reviewed の Forest Shuffle で、公開 description / summary が
-- canonical metadata と source-bound RuleSet に反する旧情報を含まないこと。
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
    RAISE NOTICE 'Forest Shuffle canonical game row is not part of the fixture; skipping summary alignment';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Forest Shuffle game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND verification_status = 'source_bound'
    AND edition_label = 'Lookout Forest Shuffle base game 2023 / current official rules'
    AND platform = 'physical'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Current source-bound Forest Shuffle RuleSet is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'human_reviewed'
      AND min_players = 2
      AND max_players = 5
      AND play_time = 60
      AND play_time_min_minutes = 60
      AND play_time_max_minutes = 60
      AND min_age = 10
      AND published_year = 2023
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Forest Shuffle reviewed identity or canonical metadata changed; re-audit before changing public summary';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Forest Shuffle trusted public summary requires exactly 9 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Forest Shuffle trusted public summary requires exactly 9 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Forest Shuffle trusted public summary requires exactly 9 supporting EvidenceBindings, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND rule_id = 'build-forest'
      AND normalized_statement = 'プレイヤーは木と生物を自分の森へ配置し、ゲーム終了時に最も高い得点を得ることを目指す。'
  ) OR NOT EXISTS (
    SELECT 1
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND rule_id = 'highest-score-wins'
      AND normalized_statement = '森の見えているカードの得点とcave内カードの得点を合計し、最も高い得点のプレイヤーが勝つ。'
  ) THEN
    RAISE EXCEPTION 'Forest Shuffle summary authority changed; re-audit before publishing summary';
  END IF;

  UPDATE public.games
  SET description = '木と生物を自分の森へ配置し、ゲーム終了時に森の見えているカードとcave内カードの得点を合計して最高得点を競う、2～5人・60分・10歳以上のカードゲームです。',
      summary = '木と生物を森へ配置し、ゲーム終了時の合計得点が最も高いプレイヤーが勝つカードゲーム。2～5人・60分・10歳以上。',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND description = '木と生物を自分の森へ配置し、ゲーム終了時に森の見えているカードとcave内カードの得点を合計して最高得点を競う、2～5人・60分・10歳以上のカードゲームです。'
      AND summary = '木と生物を森へ配置し、ゲーム終了時の合計得点が最も高いプレイヤーが勝つカードゲーム。2～5人・60分・10歳以上。'
      AND description NOT LIKE '%40〜60分%'
      AND summary NOT LIKE '%40〜60分%'
  ) THEN
    RAISE EXCEPTION 'Forest Shuffle public summary alignment failed';
  END IF;
END $$;

COMMIT;
