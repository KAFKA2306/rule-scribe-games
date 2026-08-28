BEGIN;

-- プレイヤー向け完了条件:
-- ディズニー・ロルカナ日本語版は、現在のタカラトミー公式総合ルール
-- バージョン2.2.0（2026年7月10日施行）に結び付いた基本ルール10件が
-- すべて確認できる場合だけ検索対象へ戻す。
-- 日本語版は2025年発売として扱い、大会の1ラウンド25分を通常プレイ時間として表示しない。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'disney-lorcana'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Disney Lorcana game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = '日本語版 TCG'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = 'cr-2.2.0-ja-2026-07-10'
    AND COALESCE(source_revision, '') = 'Disney Lorcana Comprehensive Rules 2.2.0 (effective 2026-07-10)'
    AND effective_date = DATE '2026-07-10'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Disney Lorcana Japanese Comprehensive Rules 2.2.0 RuleSet is required';
  END IF;

  IF (
    SELECT count(*) FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 10 THEN
    RAISE EXCEPTION 'Disney Lorcana requires exactly 10 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*) FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 10 THEN
    RAISE EXCEPTION 'Disney Lorcana requires exactly 10 accepted rule claims';
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
    RAISE EXCEPTION 'Disney Lorcana requires exactly 10 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Disney Lorcana RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:takaratomy:lorcana:cr-2.2.0-ja'
  ) THEN
    RAISE EXCEPTION 'Disney Lorcana rules must use only the official Japanese Comprehensive Rules 2.2.0 source';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:takaratomy:lorcana:japanese-official'
      AND url = 'https://www.takaratomy.co.jp/products/disneylorcana/'
      AND publisher_name = 'Takara Tomy / Ravensburger'
      AND source_type = 'publisher_product_page'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND revision_label = 'current'
  ) THEN
    RAISE EXCEPTION 'Takara Tomy Disney Lorcana Japanese product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:takaratomy:lorcana:cr-2.2.0-ja'
      AND url = 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710='
      AND publisher_name = 'Takara Tomy / Ravensburger'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND revision_label = '2.2.0-effective-2026-07-10'
      AND COALESCE(trust_metadata ->> 'living_document', 'false') = 'true'
      AND COALESCE(trust_metadata ->> 'effective_date', '') = '2026-07-10'
  ) THEN
    RAISE EXCEPTION 'Takara Tomy Disney Lorcana Japanese Comprehensive Rules 2.2.0 source is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:takaratomy:lorcana:japanese-official',
      'publisher:takaratomy:lorcana:cr-2.2.0-ja'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Disney Lorcana RuleSet must preserve product identity and revisioned rulebook source distinctions';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      title_ja = 'ディズニー・ロルカナ',
      edition_label = '日本語版 TCG',
      publisher = 'Takara Tomy / Ravensburger',
      published_year = 2025,
      min_players = 2,
      max_players = NULL,
      play_time = NULL,
      play_time_min_minutes = NULL,
      play_time_max_minutes = NULL,
      min_age = 8,
      source_revision = 'Disney Lorcana Comprehensive Rules 2.2.0 (effective 2026-07-10)',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"disney_lorcana_japanese_tcg_cr_2_2_0"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:takaratomy:lorcana:japanese-official',
    'publisher:takaratomy:lorcana:cr-2.2.0-ja'
  );
END $$;

COMMIT;
