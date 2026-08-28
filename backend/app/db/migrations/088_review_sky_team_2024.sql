BEGIN;

-- プレイヤー向け完了条件:
-- スカイチーム日本語版（2024年6月）の基本ゲーム13ルールが、
-- Le Scorpion Masqué公式の基本ルール「Landing Procedure」にすべて結び付き、
-- 追加フライト「乱気流」などの拡張ルールを含まない場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'sky-team'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Sky Team game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'スカイチーム 日本語版（2024年6月）'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = 'landing-procedure-2023-06-06-ja-2024-06'
    AND COALESCE(source_revision, '') = 'Scorpion Masqué Landing Procedure 2023-06-06 + Sugorokuya Japanese edition identity; audited 2026-08-24'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Sky Team Japanese 2024 RuleSet is required';
  END IF;

  IF (
    SELECT count(*) FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 13 THEN
    RAISE EXCEPTION 'Sky Team requires exactly 13 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*) FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 13 THEN
    RAISE EXCEPTION 'Sky Team requires exactly 13 accepted rule claims';
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
    RAISE EXCEPTION 'Sky Team requires exactly 13 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Sky Team RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:scorpion:sky-team:landing-procedure'
  ) THEN
    RAISE EXCEPTION 'Sky Team base rules must use only the official Landing Procedure source';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'localizer:sugorokuya:sky-team:product'
      AND url = 'https://sugorokuya.jp/p/sky-team'
      AND publisher_name = 'すごろくや'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND revision_label = 'jp-edition-2024-06'
  ) THEN
    RAISE EXCEPTION 'Sugorokuya Sky Team Japanese product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:scorpion:sky-team:landing-procedure'
      AND url = 'https://www.scorpionmasque.com/sites/scorpionmasque.com/files/st_rules01_en_06jun2023.pdf'
      AND publisher_name = 'Le Scorpion Masqué'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND language_code = 'en'
      AND revision_label = 'landing-procedure-2023-06-06'
  ) THEN
    RAISE EXCEPTION 'Le Scorpion Masque Sky Team base Landing Procedure source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:scorpion:sky-team:product'
      AND url = 'https://www.scorpionmasque.com/en/sky-team'
      AND publisher_name = 'Le Scorpion Masqué'
      AND source_type = 'publisher_product_page'
      AND platform = 'physical'
      AND language_code = 'en'
      AND revision_label = 'current-base-game'
  ) THEN
    RAISE EXCEPTION 'Le Scorpion Masque Sky Team base product source is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'localizer:sugorokuya:sky-team:product',
      'publisher:scorpion:sky-team:landing-procedure',
      'publisher:scorpion:sky-team:product'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Sky Team RuleSet must preserve Japanese product identity and base rulebook source distinctions';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM unnest((SELECT source_ids FROM public.rule_sets WHERE id = v_ruleset_id)) AS source_id
    WHERE lower(source_id) LIKE '%turbulence%'
       OR lower(source_id) LIKE '%alarm%'
  ) THEN
    RAISE EXCEPTION 'Sky Team base RuleSet must not include expansion sources';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      title_ja = 'スカイチーム',
      edition_label = 'スカイチーム 日本語版（2024年6月）',
      publisher = 'すごろくや / Le Scorpion Masqué',
      published_year = 2024,
      min_players = 2,
      max_players = 2,
      play_time = 20,
      min_age = 12,
      source_revision = 'Scorpion Masqué Landing Procedure 2023-06-06 + Sugorokuya Japanese edition identity; audited 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"sky_team_japanese_2024_base_game"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'localizer:sugorokuya:sky-team:product',
    'publisher:scorpion:sky-team:landing-procedure',
    'publisher:scorpion:sky-team:product'
  );
END $$;

COMMIT;
