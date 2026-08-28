BEGIN;

-- プレイヤー向け完了条件:
-- ブラス：バーミンガム 完全日本語版（2019年11月28日）の基本ゲーム14ルールが、
-- Roxley Games公式Rulebook 2018.11.20にすべて結び付き、
-- ブラス：ランカシャーのルールを混ぜない場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'brass-birmingham'
  LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Brass: Birmingham game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'ブラス：バーミンガム 完全日本語版（2019年11月28日）'
    AND COALESCE(revision_label, '') = 'roxley-2018.11.20-ja-2019-11-28'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;
  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Brass: Birmingham RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 14 THEN
    RAISE EXCEPTION 'Brass: Birmingham requires exactly 14 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 14 THEN
    RAISE EXCEPTION 'Brass: Birmingham requires exactly 14 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
  ) <> 14 THEN
    RAISE EXCEPTION 'Brass: Birmingham requires exactly 14 supporting evidence bindings';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    LEFT JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    LEFT JOIN public.source_locators sl ON sl.locator_id = eb.locator_id
    WHERE rn.rule_set_id = v_ruleset_id
      AND (
        eb.binding_id IS NULL
        OR eb.source_id <> 'publisher:roxley:brass-birmingham:rulebook'
        OR sl.locator_id IS NULL
        OR sl.source_id <> 'publisher:roxley:brass-birmingham:rulebook'
        OR eb.locator_id NOT LIKE 'brass-birmingham:rulebook:%'
      )
  ) THEN
    RAISE EXCEPTION 'Every Brass: Birmingham rule must use the Roxley 2018.11.20 rulebook and locator';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND eb.source_id ILIKE '%lancashire%'
  ) THEN
    RAISE EXCEPTION 'Brass: Lancashire evidence must not be mixed into Brass: Birmingham';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'localizer:arclight:brass-birmingham:product'
      AND publisher_name = 'アークライト'
  ) THEN
    RAISE EXCEPTION 'Official Arclight Japanese edition identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:roxley:brass-birmingham:product'
      AND publisher_name = 'Roxley Games'
  ) THEN
    RAISE EXCEPTION 'Official Roxley product source is required';
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
    RAISE EXCEPTION 'Brass: Birmingham review state update failed';
  END IF;
END $$;

COMMIT;
