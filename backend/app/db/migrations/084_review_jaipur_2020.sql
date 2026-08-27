BEGIN;

-- Player-facing success condition:
-- ジャイプルの2020年ホビージャパン日本語版は、SPACE Cowboysの新装版ルールだけに
-- 結び付いた11件のルールと根拠がそろい、日本語版の商品情報が公式情報と一致する場合だけ
-- 検索対象へ戻す。旧GAMES WORK版やデジタル版の情報は混ぜない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'jaipur'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Jaipur game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'ホビージャパン日本語版 (2020 SPACE Cowboys edition)'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = '2020-space-cowboys-ja'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Jaipur 2020 Japanese physical RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 11 THEN
    RAISE EXCEPTION 'Jaipur requires exactly 11 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 11 THEN
    RAISE EXCEPTION 'Jaipur requires exactly 11 accepted rule claims';
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
    RAISE EXCEPTION 'Jaipur requires exactly 11 supporting evidence bindings';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    LEFT JOIN public.claims c
      ON c.claim_id = rn.source_claim_ref
      AND c.rule_set_id = rn.rule_set_id
      AND c.lifecycle_status = 'accepted'
    LEFT JOIN public.evidence_bindings eb
      ON eb.binding_id = rn.evidence_ref
      AND eb.claim_id = c.claim_id
      AND eb.relation = 'supports'
    WHERE rn.rule_set_id = v_ruleset_id
      AND (c.claim_id IS NULL OR eb.binding_id IS NULL)
  ) THEN
    RAISE EXCEPTION 'Every Jaipur RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:spacecowboys:jaipur:2019-rulebook'
  ) THEN
    RAISE EXCEPTION 'Jaipur rules must use only the official SPACE Cowboys 2019 new-edition rulebook';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    JOIN public.evidence_sources es ON es.source_id = eb.source_id
    WHERE rn.rule_set_id = v_ruleset_id
      AND (
        es.publisher_name <> 'SPACE Cowboys'
        OR es.source_type <> 'publisher_rulebook'
        OR es.platform <> 'physical'
      )
  ) THEN
    RAISE EXCEPTION 'Jaipur rule evidence must remain first-party SPACE Cowboys physical-rule evidence';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:hobbyjapan:jaipur:2020-product'
      AND url = 'https://hobbyjapan.games/jaipur/'
      AND publisher_name = 'Hobby Japan'
      AND source_type = 'publisher_product_page'
      AND language_code = 'ja'
      AND revision_label = '2020-09'
  ) THEN
    RAISE EXCEPTION 'Hobby Japan Jaipur 2020 Japanese product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:spacecowboys:jaipur:current-product'
      AND url = 'https://www.spacecowboys-games.com/game/jaipur/'
      AND publisher_name = 'SPACE Cowboys'
      AND source_type = 'publisher_product_page'
  ) THEN
    RAISE EXCEPTION 'SPACE Cowboys Jaipur product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:spacecowboys:jaipur:2019-rulebook'
      AND url = 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf'
      AND publisher_name = 'SPACE Cowboys'
      AND source_type = 'publisher_rulebook'
      AND language_code = 'en'
      AND revision_label = '2019-new-edition'
  ) THEN
    RAISE EXCEPTION 'SPACE Cowboys official Jaipur 2019 new-edition rulebook is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:hobbyjapan:jaipur:2020-product',
      'publisher:spacecowboys:jaipur:current-product',
      'publisher:spacecowboys:jaipur:2019-rulebook'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Jaipur RuleSet must preserve Japanese product, current product, and rulebook source distinctions';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 2,
      max_players = 2,
      play_time = 30,
      min_age = 12,
      published_year = 2020,
      source_revision = 'Hobby Japan 2020 Japanese product identity + SPACE Cowboys official 2019 new-edition rulebook; older GAMES WORK edition, digital implementations, community summaries, and variants excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Hobby Japan 2020 Japanese product identity + SPACE Cowboys official 2019 new-edition rulebook; older GAMES WORK edition, digital implementations, community summaries, and variants excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"jaipur_hobby_japan_2020_space_cowboys_physical"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:hobbyjapan:jaipur:2020-product',
    'publisher:spacecowboys:jaipur:current-product',
    'publisher:spacecowboys:jaipur:2019-rulebook'
  );
END $$;

COMMIT;
