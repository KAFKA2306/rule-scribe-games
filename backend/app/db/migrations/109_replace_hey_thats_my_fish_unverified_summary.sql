BEGIN;

-- Production read-backで、旧来の評価的なsummary/descriptionが残っていたため、
-- © 2023 Plan B Games Inc. 公式ルールブックで直接確認できる内容だけへ置換する。
DO $$
DECLARE
  v_count integer;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.games WHERE slug = 'hey-thats-my-fish') THEN
    IF current_database() = 'source_bound_ruleset_test' THEN
      RAISE NOTICE 'Hey That''s My Fish canonical game row is not part of the fixture; skipping migration';
      RETURN;
    END IF;
    RAISE EXCEPTION 'Canonical hey-thats-my-fish game row is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.games g
  JOIN public.rule_sets rs ON rs.game_id = g.id AND rs.is_active = true
  WHERE g.slug = 'hey-thats-my-fish'
    AND g.content_review_status = 'human_reviewed'
    AND g.identity_status = 'verified'
    AND rs.verification_status = 'source_bound'
    AND rs.revision_label = 'copyright-2023';

  IF v_count <> 1 THEN
    RAISE EXCEPTION 'hey-thats-my-fish requires exactly one reviewed source-bound 2023 RuleSet, found %', v_count;
  END IF;

  UPDATE public.games
  SET summary = 'ペンギンを六角形の浮氷の上で動かし、移動前の浮氷タイルを集めて魚の数を競う。ゲーム終了時に魚の合計が最も多いプレイヤーが勝つ。',
      description = 'ペンギンを六角形の浮氷の上で動かし、移動前の浮氷タイルを集めて魚の数を競う。ゲーム終了時に魚の合計が最も多いプレイヤーが勝つ。',
      updated_at = now()
  WHERE slug = 'hey-thats-my-fish';

  IF EXISTS (
    SELECT 1 FROM public.games
    WHERE slug = 'hey-thats-my-fish'
      AND (
        summary LIKE '%奥深%'
        OR summary LIKE '%サバイバル%'
        OR description LIKE '%奥深%'
        OR description LIKE '%非常に熱い%'
      )
  ) THEN
    RAISE EXCEPTION 'hey-thats-my-fish unsupported evaluative copy remains';
  END IF;
END $$;

COMMIT;
