BEGIN;

-- プレイヤー向け完了条件:
-- エルフェンランドのAMIGO Rules Version 3.0（2013）の基本ゲーム13ルールが、
-- AMIGO公式ルールブックにすべて結び付き、別版や発展ルールを基本ルールへ混ぜない場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'elfenland'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Elfenland game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'AMIGO Elfenland（Rules Version 3.0 / 2013）'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = 'amigo-v3.0-2013-ja'
    AND COALESCE(source_revision, '') = 'AMIGO Elfenland Rules Version 3.0 (2013), official Japanese/English rulebooks; audited 2026-08-24'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Elfenland Version 3.0 RuleSet is required';
  END IF;

  IF (
    SELECT count(*) FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 13 THEN
    RAISE EXCEPTION 'Elfenland requires exactly 13 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*) FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 13 THEN
    RAISE EXCEPTION 'Elfenland requires exactly 13 accepted rule claims';
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
    RAISE EXCEPTION 'Elfenland requires exactly 13 supporting evidence bindings';
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
    RAISE EXCEPTION 'Every Elfenland RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id <> 'publisher:amigo:elfenland:rules-en-v3'
  ) THEN
    RAISE EXCEPTION 'Elfenland base rule claims must use only the official AMIGO Version 3.0 rulebook evidence';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:amigo:elfenland:product'
      AND url = 'https://www.amigo-spiele.de/elfenland_2610_1110'
      AND publisher_name = 'AMIGO Spiel + Freizeit'
      AND source_type = 'publisher_product_page'
      AND platform = 'physical'
      AND language_code = 'de'
      AND revision_label = 'current-product-page'
  ) THEN
    RAISE EXCEPTION 'AMIGO Elfenland product source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:amigo:elfenland:rules-ja-v3'
      AND url = 'https://blog.amigo-spiele.de/content/ap/rule/02610-JP-AmigoRule.pdf'
      AND publisher_name = 'AMIGO Spiel + Freizeit'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND language_code = 'ja'
      AND revision_label = '3.0-2013'
  ) THEN
    RAISE EXCEPTION 'AMIGO Elfenland Japanese Version 3.0 rulebook source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'publisher:amigo:elfenland:rules-en-v3'
      AND url = 'https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf'
      AND publisher_name = 'AMIGO Spiel + Freizeit'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND language_code = 'en'
      AND revision_label = '3.0-2013'
  ) THEN
    RAISE EXCEPTION 'AMIGO Elfenland English Version 3.0 rulebook source is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:amigo:elfenland:product',
      'publisher:amigo:elfenland:rules-ja-v3',
      'publisher:amigo:elfenland:rules-en-v3'
    ]::text[] <@ source_ids
    AND source_ids <@ ARRAY[
      'publisher:amigo:elfenland:product',
      'publisher:amigo:elfenland:rules-ja-v3',
      'publisher:amigo:elfenland:rules-en-v3'
    ]::text[]
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Elfenland RuleSet source list must contain only the AMIGO product and Version 3.0 rulebooks';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      title_ja = 'エルフェンランド',
      edition_label = 'AMIGO Elfenland（Rules Version 3.0 / 2013）',
      publisher = 'AMIGO Spiel + Freizeit',
      min_players = 2,
      max_players = 6,
      play_time = NULL,
      min_age = NULL,
      published_year = NULL,
      source_revision = 'AMIGO Elfenland Rules Version 3.0 (2013), official Japanese/English rulebooks; audited 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"elfenland_amigo_rules_v3_2013"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:amigo:elfenland:product',
    'publisher:amigo:elfenland:rules-ja-v3',
    'publisher:amigo:elfenland:rules-en-v3'
  );
END $$;

COMMIT;
