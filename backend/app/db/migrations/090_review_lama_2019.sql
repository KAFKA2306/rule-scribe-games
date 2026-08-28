BEGIN;

-- プレイヤー向け完了条件:
-- LAMA（AMIGO Art.Nr.01907）の基本ゲーム9ルールが、現行のAMIGO公式Version 1.8にすべて結び付き、
-- LAMA Party / LAMA Dice / LAMA Kadabraを混ぜない場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id FROM public.games WHERE slug = 'l-l-a-m-a' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE EXCEPTION 'Canonical LAMA game row is required'; END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id AND is_active = true AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'LAMA（AMIGO Art.Nr.01907）'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;
  IF v_ruleset_id IS NULL THEN RAISE EXCEPTION 'Active source-bound LAMA RuleSet is required'; END IF;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status=('source' || '_' || 'bound')) <> 9
    THEN RAISE EXCEPTION 'LAMA requires exactly 9 source-bound RuleNodes'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 9
    THEN RAISE EXCEPTION 'LAMA requires exactly 9 accepted rule claims'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND c.target_type='rule_node' AND c.lifecycle_status='accepted' AND eb.relation='supports') <> 9
    THEN RAISE EXCEPTION 'LAMA requires exactly 9 supporting evidence bindings'; END IF;

  INSERT INTO public.evidence_sources
    (source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,retrieved_at,trust_metadata)
  VALUES
    ('publisher:amigo:lama:rules-v1.8-de',
     'https://blog.amigo-spiele.de/content/ap/rule/01907-DE-AmigoRule.pdf',
     'AMIGO LAMA Art.Nr.01907 Spielanleitung Version 1.8 (2019)',
     'publisher_rulebook','AMIGO Spiel + Freizeit GmbH','physical','de','version-1.8-2019',now(),
     '{"authority":"publisher","scope":"lama_art_nr_01907_base_game","review_date":"2026-08-28","review_status":"human_reviewed"}'::jsonb)
  ON CONFLICT (source_id) DO UPDATE SET
    url=EXCLUDED.url, document_identity=EXCLUDED.document_identity, source_type=EXCLUDED.source_type,
    publisher_name=EXCLUDED.publisher_name, platform=EXCLUDED.platform, language_code=EXCLUDED.language_code,
    revision_label=EXCLUDED.revision_label, retrieved_at=EXCLUDED.retrieved_at,
    trust_metadata=EXCLUDED.trust_metadata, updated_at=now();

  UPDATE public.evidence_bindings eb
  SET source_id='publisher:amigo:lama:rules-v1.8-de'
  FROM public.claims c
  WHERE c.claim_id=eb.claim_id AND c.rule_set_id=v_ruleset_id
    AND c.target_type='rule_node' AND c.lifecycle_status='accepted' AND eb.relation='supports';

  UPDATE public.rule_nodes
  SET source_url='https://blog.amigo-spiele.de/content/ap/rule/01907-DE-AmigoRule.pdf', updated_at=now()
  WHERE rule_set_id=v_ruleset_id;

  UPDATE public.rule_sets
  SET revision_label='amigo-01907-v1.8-2019-de',
      source_revision='AMIGO LAMA Art.Nr.01907, German Rules Version 1.8 (2019); Party/Dice/Kadabra excluded; audited 2026-08-28',
      source_ids=ARRAY['publisher:amigo:lama:rules-v1.8-de','publisher:amigo:lama:rules-index']::text[],
      updated_at=now()
  WHERE id=v_ruleset_id;

  IF EXISTS (
    SELECT 1 FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id=rn.evidence_ref
    WHERE rn.rule_set_id=v_ruleset_id AND eb.source_id <> 'publisher:amigo:lama:rules-v1.8-de'
  ) THEN RAISE EXCEPTION 'Every LAMA rule must use the current AMIGO Version 1.8 rulebook'; END IF;

  UPDATE public.games
  SET content_review_status='human_reviewed', title_ja='ラマ', edition_label='LAMA（AMIGO Art.Nr.01907）',
      publisher='AMIGO Spiel + Freizeit', min_players=2, max_players=6, play_time=20, min_age=8, published_year=2019,
      source_revision='AMIGO LAMA Art.Nr.01907, German Rules Version 1.8 (2019); Party/Dice/Kadabra excluded; audited 2026-08-28',
      updated_at=now()
  WHERE id=v_game_id;
END $$;

COMMIT;
