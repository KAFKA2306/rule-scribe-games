BEGIN;

-- プレイヤー向け完了条件:
-- アズール：シントラのステンドグラスのホビージャパン日本語版 (2019) は、
-- 公式の商品情報とNext Move Games公式ルールブックに結び付いた基本ルール10件が
-- すべて確認でき、公式プレイ時間30～45分を保持する場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'azul-stained-glass-of-sintra'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Azul Stained Glass of Sintra game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = 'source_bound'
    AND COALESCE(edition_label, '') = 'ホビージャパン日本語版 (2019)'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = '2019-hobbyjapan-ja'
    AND COALESCE(variant_label, '') = ''
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Azul Sintra 2019 Japanese physical RuleSet is required';
  END IF;

  IF (
    SELECT count(*) FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = 'source_bound'
  ) <> 10 THEN
    RAISE EXCEPTION 'Azul Sintra requires exactly 10 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*) FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 10 THEN
    RAISE EXCEPTION 'Azul Sintra requires exactly 10 accepted rule claims';
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
    RAISE EXCEPTION 'Azul Sintra requires exactly 10 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Azul Sintra RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:nextmove:azul-sintra:official-rulebook'
  ) THEN
    RAISE EXCEPTION 'Azul Sintra rules must use only the official Next Move Games rulebook';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:hobbyjapan:azul-sintra:2019-product'
      AND url = 'https://hobbyjapan.games/azul_stained_glass_of_sintra/'
      AND publisher_name = 'Hobby Japan / Next Move Games'
      AND source_type = 'publisher_product_page'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND revision_label = '2019-02'
  ) THEN
    RAISE EXCEPTION 'Hobby Japan Azul Sintra 2019 Japanese product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:nextmove:azul-sintra:official-rulebook'
      AND url = 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf'
      AND publisher_name = 'Next Move Games'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND language_code = 'en'
      AND revision_label = 'current-hosted-copy'
  ) THEN
    RAISE EXCEPTION 'Next Move Games Azul Sintra official rulebook is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:hobbyjapan:azul-sintra:2019-product',
      'publisher:nextmove:azul-sintra:official-rulebook'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Azul Sintra RuleSet must preserve Japanese product identity and rulebook source distinctions';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      edition_label = 'ホビージャパン日本語版 (2019)',
      publisher = 'Hobby Japan / Next Move Games',
      published_year = 2019,
      min_players = 2,
      max_players = 4,
      play_time_min_minutes = 30,
      play_time_max_minutes = 45,
      min_age = 8,
      source_revision = 'Hobby Japan 2019 Japanese product identity + Next Move Games current-hosted official rulebook; base physical game only; other Azul titles, expansions, digital adaptations, and community summaries excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Hobby Japan 2019 Japanese product identity + Next Move Games current-hosted official rulebook; base physical game only; other Azul titles, expansions, digital adaptations, and community summaries excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"azul_sintra_hobbyjapan_2019_physical_base"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:hobbyjapan:azul-sintra:2019-product',
    'publisher:nextmove:azul-sintra:official-rulebook'
  );
END $$;

COMMIT;
