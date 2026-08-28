BEGIN;

-- プレイヤー向け完了条件:
-- ドミニオン：第二版（ホビージャパン日本語版）の基本ゲーム10ルールが、
-- Rio Grande Games公式Dominion Second Edition rulebook（2021 printing）にすべて結び付き、
-- 別の拡張セットを混ぜない場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'dominion'
  LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Dominion Second Edition game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'ドミニオン：第二版（ホビージャパン日本語版）'
    AND COALESCE(revision_label, '') = 'dominion-2e-rules-2021'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;
  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Dominion Second Edition RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 10 THEN
    RAISE EXCEPTION 'Dominion Second Edition requires exactly 10 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 10 THEN
    RAISE EXCEPTION 'Dominion Second Edition requires exactly 10 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
  ) <> 10 THEN
    RAISE EXCEPTION 'Dominion Second Edition requires exactly 10 supporting evidence bindings';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    LEFT JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    LEFT JOIN public.source_locators sl ON sl.locator_id = eb.locator_id
    WHERE rn.rule_set_id = v_ruleset_id
      AND (
        eb.binding_id IS NULL
        OR eb.source_id <> 'publisher:rio-grande:dominion-2e-rules-2021'
        OR sl.locator_id IS NULL
        OR sl.source_id <> 'publisher:rio-grande:dominion-2e-rules-2021'
      )
  ) THEN
    RAISE EXCEPTION 'Every Dominion Second Edition rule must use the Rio Grande Games 2021 rulebook and locator';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.lifecycle_status = 'accepted'
      AND eb.source_id <> 'publisher:rio-grande:dominion-2e-rules-2021'
  ) THEN
    RAISE EXCEPTION 'Dominion expansion or unrelated evidence must not be mixed into the base Second Edition rules';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:hobbyjapan:dominion-2e-ja'
      AND publisher_name = 'Hobby Japan'
      AND url = 'https://hobbyjapan.games/dominion_2nd/'
  ) THEN
    RAISE EXCEPTION 'Official Hobby Japan Dominion Second Edition identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:rio-grande:dominion-2e-rules-2021'
      AND publisher_name = 'Rio Grande Games'
      AND revision_label = '2021-rulebook-printing'
  ) THEN
    RAISE EXCEPTION 'Official Rio Grande Games Dominion Second Edition 2021 rulebook is required';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      updated_at = now()
  WHERE id = v_game_id;

  IF (
    SELECT content_review_status
    FROM public.games
    WHERE id = v_game_id
  ) <> 'human_reviewed' THEN
    RAISE EXCEPTION 'Dominion Second Edition review state update failed';
  END IF;
END $$;

COMMIT;
