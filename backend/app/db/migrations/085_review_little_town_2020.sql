BEGIN;

-- プレイヤー向け完了条件:
-- リトルタウンビルダーズのアークライト日本語リメイク版 (2020) は、
-- 公式の商品情報と、IELLO公式ルールブックに結び付いた共有基本ルール10件が
-- すべて確認できる場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'little-town'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Little Town game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = 'source_bound'
    AND COALESCE(edition_label, '') = 'アークライト日本語リメイク版 (2020)'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = '2020-arclight-remake'
    AND COALESCE(variant_label, '') = ''
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Little Town 2020 Japanese physical RuleSet is required';
  END IF;

  IF (
    SELECT count(*) FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = 'source_bound'
  ) <> 10 THEN
    RAISE EXCEPTION 'Little Town requires exactly 10 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*) FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 10 THEN
    RAISE EXCEPTION 'Little Town requires exactly 10 accepted rule claims';
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
    RAISE EXCEPTION 'Little Town requires exactly 10 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Little Town RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:iello:little-town:2019-rulebook'
  ) THEN
    RAISE EXCEPTION 'Little Town shared core rules must use only the official IELLO 2019 rulebook';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    JOIN public.evidence_sources es ON es.source_id = eb.source_id
    WHERE rn.rule_set_id = v_ruleset_id
      AND (
        es.publisher_name <> 'IELLO'
        OR es.source_type <> 'publisher_rulebook'
        OR es.platform <> 'physical'
        OR es.language_code <> 'en'
        OR es.revision_label <> '2019-international-remake'
      )
  ) THEN
    RAISE EXCEPTION 'Little Town rule evidence must remain IELLO 2019 physical rulebook evidence';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:arclight:little-town:2020-product'
      AND url = 'https://arclightgames.jp/product/%E3%83%AA%E3%83%88%E3%83%AB%E3%82%BF%E3%82%A6%E3%83%B3%E3%83%93%E3%83%AB%E3%83%80%E3%83%BC%E3%82%BA/'
      AND publisher_name = 'Arclight'
      AND source_type = 'publisher_product_page'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND revision_label = '2020-01-23'
  ) THEN
    RAISE EXCEPTION 'Arclight Little Town 2020 Japanese product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'designer:studiogg:little-town:2017-official'
      AND url = 'https://studiogg.doorblog.jp/archives/cat_1309479.html'
      AND publisher_name = 'Studio GG'
      AND source_type = 'designer_official_page'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND revision_label = '2017-original'
  ) THEN
    RAISE EXCEPTION 'Studio GG Little Town 2017 lineage source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:iello:little-town:2019-rulebook'
      AND url = 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf'
      AND publisher_name = 'IELLO'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND language_code = 'en'
      AND revision_label = '2019-international-remake'
  ) THEN
    RAISE EXCEPTION 'IELLO Little Town official 2019 rulebook is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:arclight:little-town:2020-product',
      'designer:studiogg:little-town:2017-official',
      'publisher:iello:little-town:2019-rulebook'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Little Town RuleSet must preserve product, lineage, and rulebook source distinctions';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      edition_label = 'アークライト日本語リメイク版 (2020)',
      publisher = 'Arclight / Studio GG',
      published_year = 2020,
      min_players = 2,
      max_players = 4,
      play_time = 30,
      min_age = 8,
      source_revision = 'Arclight 2020 Japanese remake identity + Studio GG lineage + IELLO 2019 official shared-core rulebook; edition-specific additions, expansions, digital adaptations, and community summaries excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Arclight 2020 Japanese remake identity + Studio GG lineage + IELLO 2019 official shared-core rulebook; edition-specific additions, expansions, digital adaptations, and community summaries excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"little_town_arclight_2020_physical_shared_core"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:arclight:little-town:2020-product',
    'designer:studiogg:little-town:2017-official',
    'publisher:iello:little-town:2019-rulebook'
  );
END $$;

COMMIT;
