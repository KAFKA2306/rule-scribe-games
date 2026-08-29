BEGIN;

-- プレイヤー向け成功条件:
-- 外部流入から横濱紳商伝デュエルへ到達しても、一次資料へ結び付いていない旧rules_contentを
-- 確定ルールとして表示しない。確認済みRuleSetがない間はreview_requiredのままfail-closedする。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'yokohama-duel'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Yokohama Duel canonical game row is not part of the fixture; skipping';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Yokohama Duel game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND identity_status = 'unverified'
      AND source_trust = 'unknown'
      AND source_url = 'http://okazubrand.jimdofree.com/'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
      AND rules_content IS NOT NULL
      AND btrim(rules_content) <> ''
  ) THEN
    RAISE EXCEPTION 'Yokohama Duel trust state or legacy rule state changed; re-audit before migration';
  END IF;

  SELECT count(*) INTO v_ruleset_count
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active';

  IF v_ruleset_count <> 0 THEN
    RAISE EXCEPTION 'Yokohama Duel now has an active RuleSet; migrate from that authority instead of clearing legacy rules';
  END IF;

  UPDATE public.games
  SET rules_content = NULL,
      content_review_status = 'review_required',
      description = '「横濱紳商伝デュエル」は現在、公開ルールの一次資料との照合が未完了です。確認できていないルール本文は掲載せず、公式資料を確認できるまで未確認として扱います。',
      summary = '公開ルールの一次資料との照合が未完了です。確認できていないルール本文は掲載していません。',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND rules_content IS NULL
      AND content_review_status = 'review_required'
      AND identity_status = 'unverified'
      AND source_trust = 'unknown'
      AND description = '「横濱紳商伝デュエル」は現在、公開ルールの一次資料との照合が未完了です。確認できていないルール本文は掲載せず、公式資料を確認できるまで未確認として扱います。'
      AND summary = '公開ルールの一次資料との照合が未完了です。確認できていないルール本文は掲載していません。'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Yokohama Duel fail-closed migration did not reach the required state';
  END IF;
END $$;

COMMIT;
