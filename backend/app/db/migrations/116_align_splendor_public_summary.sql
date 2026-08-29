BEGIN;

-- プレイヤー向け成功条件:
-- 398 views の「宝石の煌き」公開ページで、2024年改訂版の公式情報だけを要約し、
-- 検証対象でない評価語をSEO・SNS・GamePageへ流さないこと。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'splendor'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Splendor canonical game row is not part of the fixture; skipping summary alignment';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Splendor game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND title_ja = '宝石の煌き'
      AND identity_status = 'verified'
      AND identity_source = 'https://hobbyjapan.games/splendor/'
      AND source_url = 'https://hobbyjapan.games/splendor/'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'human_reviewed'
      AND min_players = 2
      AND max_players = 4
      AND play_time = 30
      AND play_time_min_minutes = 30
      AND play_time_max_minutes = 30
      AND min_age = 10
      AND published_year = 2024
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Splendor reviewed 2024 identity, metadata, or monetization path changed; re-audit before changing public summary';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = 'source_bound'
    AND language_code = 'ja'
    AND platform = 'physical'
    AND edition_label = 'ホビージャパン日本語版 改訂版 (2024)'
    AND revision_label = '2024-refresh'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Current source-bound Splendor 2024 RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 14 THEN
    RAISE EXCEPTION 'Splendor trusted public summary requires exactly 14 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 14 THEN
    RAISE EXCEPTION 'Splendor trusted public summary requires exactly 14 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 14 THEN
    RAISE EXCEPTION 'Splendor trusted public summary requires exactly 14 supporting EvidenceBindings, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND rule_id = 'game-end.trigger'
      AND normalized_statement = 'ターン終了時に威信ポイントが15点以上になったプレイヤーが出るとゲーム終了が発動し、全員の手番数が同じになるまで続ける。'
  ) OR NOT EXISTS (
    SELECT 1 FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND rule_id = 'victory.most-prestige'
      AND normalized_statement = 'ゲーム終了時に威信ポイントが最も高いプレイヤーが勝者となる。'
  ) OR NOT EXISTS (
    SELECT 1 FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND rule_id = 'effect.development-bonus'
      AND normalized_statement = '獲得した発展カードのボーナスは、以後その色のカード購入コストをボーナス1つにつき宝石1個分減らす。'
  ) THEN
    RAISE EXCEPTION 'Splendor summary authority changed; re-audit before publishing summary';
  END IF;

  UPDATE public.games
  SET description = '「宝石の煌き」は、宝石・黄金トークンで発展カードを購入し、そのボーナスで後の購入コストを減らしながら威信ポイントを集める、2～4人・約30分・10歳以上のゲームです。条件を満たすと貴族の訪問を受け、いずれかのプレイヤーが15威信ポイントに達したラウンドの終了時に勝者を決めます。',
      summary = '宝石トークンで発展カードを購入し、ボーナスと貴族で威信ポイントを集める。15威信ポイント到達後、そのラウンド終了時に最も高い威信ポイントのプレイヤーが勝つ。2～4人・約30分・10歳以上。',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND description = '「宝石の煌き」は、宝石・黄金トークンで発展カードを購入し、そのボーナスで後の購入コストを減らしながら威信ポイントを集める、2～4人・約30分・10歳以上のゲームです。条件を満たすと貴族の訪問を受け、いずれかのプレイヤーが15威信ポイントに達したラウンドの終了時に勝者を決めます。'
      AND summary = '宝石トークンで発展カードを購入し、ボーナスと貴族で威信ポイントを集める。15威信ポイント到達後、そのラウンド終了時に最も高い威信ポイントのプレイヤーが勝つ。2～4人・約30分・10歳以上。'
      AND description NOT LIKE '%傑作%'
      AND summary NOT LIKE '%頂点%'
  ) THEN
    RAISE EXCEPTION 'Splendor public summary alignment failed';
  END IF;
END $$;

COMMIT;
