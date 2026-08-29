BEGIN;

-- プレイヤー向け成功条件:
-- 「ピリピリ」のページ全体の要約でBGA版の終了条件を一般ルールとして見せず、
-- 物理版とBoard Game Arena版のRuleSetが別であることを明示する。
-- Claim/Evidenceへ結び付いていない攻略・注意事項・用語ルールも公開しない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_count integer;
  v_physical_count integer;
  v_bga_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'pili-pili'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Pili Pili canonical game row is not part of the fixture; skipping';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Pili Pili game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND identity_status = 'verified'
      AND identity_source = 'https://atmgaming.com/product/pili-pili'
      AND source_trust = 'authorized_partner'
      AND source_url = 'https://ja.boardgamearena.com/gamepanel?game=pilipili'
      AND content_review_status = 'review_required'
      AND rules_content IS NULL
      AND setup_summary IS NULL
      AND gameplay_summary IS NULL
      AND end_game_summary IS NULL
      AND summary = '取るトリック数を先にベットし、実際の獲得数をぴったり合わせる予想型トリックテイキング。BGA版では毎ラウンドのミッションで条件が変わり、ベットとの差だけピリを受け取ります。誰かが6ピリに達すると終了し、最少ピリが勝利です。'
  ) THEN
    RAISE EXCEPTION 'Pili Pili canonical public state changed; re-audit before migration';
  END IF;

  SELECT count(*) INTO v_ruleset_count
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = 'source_bound';

  SELECT count(*) INTO v_physical_count
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = 'source_bound'
    AND edition_label = 'ATM Gaming physical product'
    AND platform = 'physical'
    AND source_ids @> ARRAY['publisher:atm:pili-pili:current']::text[];

  SELECT count(*) INTO v_bga_count
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = 'source_bound'
    AND edition_label = 'BGA implementation'
    AND platform = 'Board Game Arena'
    AND revision_label = '260623-1715'
    AND source_ids @> ARRAY['bga:pili-pili:260623-1715']::text[];

  IF v_ruleset_count <> 2 OR v_physical_count <> 1 OR v_bga_count <> 1 THEN
    RAISE EXCEPTION 'Pili Pili RuleSet boundary changed; expected one physical and one BGA source-bound RuleSet';
  END IF;

  UPDATE public.games
  SET summary = '物理版とBoard Game Arena版では構成物と一部ルールが異なります。版を混ぜず、利用するRuleSetの版・プラットフォームを確認して参照してください。',
      description = '取るトリック数を先に予想するトリックテイキングです。物理版とBoard Game Arena版は別のRuleSetとして管理しており、構成物と一部ルールの差を混在させません。',
      structured_data = COALESCE(structured_data, '{}'::jsonb)
        - 'keywords'
        - 'pro_tips'
        - 'rule_mistakes'
        - 'strategy_analysis',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'review_required'
      AND rules_content IS NULL
      AND summary = '物理版とBoard Game Arena版では構成物と一部ルールが異なります。版を混ぜず、利用するRuleSetの版・プラットフォームを確認して参照してください。'
      AND description = '取るトリック数を先に予想するトリックテイキングです。物理版とBoard Game Arena版は別のRuleSetとして管理しており、構成物と一部ルールの差を混在させません。'
      AND NOT (COALESCE(structured_data, '{}'::jsonb) ?| ARRAY['keywords', 'pro_tips', 'rule_mistakes', 'strategy_analysis'])
  ) THEN
    RAISE EXCEPTION 'Pili Pili public projection cleanup did not reach the required state';
  END IF;
END $$;

COMMIT;
