BEGIN;

-- プレイヤー向け完了条件:
-- コヨーテ（ニューゲームズオーダー日本語版）の基本ルール13件が、
-- ニューゲームズオーダー公式日本語ルールまたは公式FAQにすべて結び付き、
-- 公式商品情報の2～10人・15～30分・10歳以上を保持できる場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'coyote'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Coyote game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'コヨーテ（ニューゲームズオーダー日本語版）'
    AND COALESCE(revision_label, '') = 'ngo-ja-rulebook-2026-02-20'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Coyote Japanese RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 13 THEN
    RAISE EXCEPTION 'Coyote requires exactly 13 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 13 THEN
    RAISE EXCEPTION 'Coyote requires exactly 13 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
  ) <> 13 THEN
    RAISE EXCEPTION 'Coyote requires exactly 13 supporting evidence bindings';
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
        'publisher:ngo:coyote:rulebook-ja',
        'publisher:ngo:coyote:product-ja'
      )
  ) THEN
    RAISE EXCEPTION 'Coyote unrelated evidence must not be mixed into the reviewed rules';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
      AND eb.source_id = 'publisher:ngo:coyote:rulebook-ja'
  ) <> 12 THEN
    RAISE EXCEPTION 'Coyote requires exactly 12 rulebook-backed rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
      AND eb.source_id = 'publisher:ngo:coyote:product-ja'
  ) <> 1 THEN
    RAISE EXCEPTION 'Coyote requires exactly one official FAQ-backed clarification';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:ngo:coyote:product-ja'
      AND publisher_name = 'ニューゲームズオーダー'
      AND source_type = 'publisher_product_page'
      AND url = 'https://www.newgamesorder.jp/games/coyote'
      AND revision_label = 'current-product-page'
  ) THEN
    RAISE EXCEPTION 'Official New Games Order Coyote product source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:ngo:coyote:rulebook-ja'
      AND publisher_name = 'ニューゲームズオーダー'
      AND source_type = 'publisher_rulebook'
      AND url = 'https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view'
      AND revision_label = 'hosted-2026-02-20'
  ) THEN
    RAISE EXCEPTION 'Official New Games Order Coyote Japanese rulebook source is required';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 2,
      max_players = 10,
      play_time = 30,
      play_time_min_minutes = 15,
      play_time_max_minutes = 30,
      min_age = 10,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND min_players = 2
      AND max_players = 10
      AND play_time = 30
      AND play_time_min_minutes = 15
      AND play_time_max_minutes = 30
      AND min_age = 10
  ) THEN
    RAISE EXCEPTION 'Coyote review or official product metadata update failed';
  END IF;
END $$;

COMMIT;
