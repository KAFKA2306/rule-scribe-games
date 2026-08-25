BEGIN;

-- Canonical scope: Wing_ Join Wars live VRChat world, base game only.
-- Only the creator/platform statements that remain stable across live updates are normalized here.
-- Detailed setup, simultaneous-turn behavior, resource carry-over, fixed turn counts, and strategy claims are removed rather than inferred.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'platform:vrchat:join-wars:world',
  'https://vrchat.com/home/world/wrld_df24020d-d60c-404a-b20f-51b37220ee40',
  '[Game] Join Wars [JP.EN.KR.CN] — VRChat world by Wing_',
  'platform_listing','Wing_','VRChat','mul','live-world-current',
  '{"authority":"creator_platform_listing","audit_date":"2026-08-25","scope":"identity_player_count_genre"}'::jsonb
),
(
  'creator:wing:join-wars:vazar',
  'https://vazar.jp/product/%E3%80%8Ajoin-wars%E3%80%8Bsupporter-card-pack/',
  'Join Wars — Wing Assembler creator storefront description',
  'creator_storefront','Wing_','VRChat','ja','current-storefront',
  '{"authority":"creator_storefront","audit_date":"2026-08-25","scope":"base_core_loop_and_tutorial"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('join-wars:world:identity','platform:vrchat:join-wars:world',NULL,'Description','created by Wing_; 1–4 player card game; deck-building and re-destructing; VRChat Join Wars theme'),
('join-wars:vazar:buy','creator:wing:join-wars:vazar',NULL,'ジャンル','buy new cards from the Booth'),
('join-wars:vazar:modify','creator:wing:join-wars:vazar',NULL,'ジャンル','add modifications/effects to cards to build stronger cards'),
('join-wars:vazar:join','creator:wing:join-wars:vazar',NULL,'ジャンル','Join developed cards to event worlds, destructing them from the deck to gain popularity points'),
('join-wars:vazar:tutorial','creator:wing:join-wars:vazar',NULL,'ワールド内チュートリアル','interactive tutorial is provided inside the live world')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='join-wars' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Join Wars canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Join Wars Work row is required'; END IF;

  UPDATE public.games SET
    title='Join Wars',title_ja='ジョインウォーズ',title_en='Join Wars',
    description='VRChatの「Join戦争」をテーマにした1～4人用のデッキ構築・再破壊カードゲーム。カードを購入して改変し、育てたカードをイベントワールドへJoinして人気点を得る。',
    summary='ブースでカードを購入し、改変でカードを強化し、育てたカードをイベントワールドへJoinして人気点を得るVRChatカードゲーム。詳細ルールはライブワールド内チュートリアルを参照する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://vrchat.com/home/world/wrld_df24020d-d60c-404a-b20f-51b37220ee40',
    source_url='https://vazar.jp/product/%E3%80%8Ajoin-wars%E3%80%8Bsupporter-card-pack/',
    official_url='https://vrchat.com/home/world/wrld_df24020d-d60c-404a-b20f-51b37220ee40',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='Join Wars（VRChat live world）',language_code='ja',publisher='Wing_',
    source_revision='Live VRChat world and Wing Assembler creator storefront; stable core loop only; detailed live rules remain in-world; audited 2026-08-25',
    min_players=1,max_players=4,play_time=60,min_age=NULL,
    amazon_url=NULL,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Join Wars（VRChat live world）'
    AND COALESCE(platform,'')='VRChat'
    AND COALESCE(revision_label,'')='live-core-2026-08-25'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','Join Wars（VRChat live world）',
      'Live VRChat world and Wing Assembler creator storefront; stable core loop only; detailed live rules remain in-world; audited 2026-08-25',
      true,'live-core-2026-08-25','VRChat','Wing_','active','source_bound',
      ARRAY['platform:vrchat:join-wars:world','creator:wing:join-wars:vazar']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Live VRChat world and Wing Assembler creator storefront; stable core loop only; detailed live rules remain in-world; audited 2026-08-25',
      publisher_name='Wing_',status='active',verification_status='source_bound',
      source_ids=ARRAY['platform:vrchat:join-wars:world','creator:wing:join-wars:vazar']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'action.buy','action','「ブース」から新しいカードを購入してデッキへ加える。',10,'source_bound','join-wars:rule:action.buy','join-wars:binding:action.buy','https://vazar.jp/product/%E3%80%8Ajoin-wars%E3%80%8Bsupporter-card-pack/','join-wars:vazar:buy','{}'::jsonb),
  (v_ruleset_id,'action.modify','action','カードへ改変を加えて効果を追加し、カードを強化する。',20,'source_bound','join-wars:rule:action.modify','join-wars:binding:action.modify','https://vazar.jp/product/%E3%80%8Ajoin-wars%E3%80%8Bsupporter-card-pack/','join-wars:vazar:modify','{}'::jsonb),
  (v_ruleset_id,'action.join','action','育てたカードをイベントワールドへ「Join」すると、そのカードはデッキから破壊され、人気点を得る。',30,'source_bound','join-wars:rule:action.join','join-wars:binding:action.join','https://vazar.jp/product/%E3%80%8Ajoin-wars%E3%80%8Bsupporter-card-pack/','join-wars:vazar:join','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'join-wars:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"creator_source_normalization","audit_date":"2026-08-25","scope":"join_wars_live_core"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'join-wars:binding:'||rn.rule_id,'join-wars:rule:'||rn.rule_id,'creator:wing:join-wars:vazar',
    rn.source_locator,'supports','{"review":"creator_storefront"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 3 THEN RAISE EXCEPTION 'Join Wars source-bound RuleNode count must be 3'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 3 THEN RAISE EXCEPTION 'Join Wars accepted Claim count must be 3'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 3 THEN RAISE EXCEPTION 'Join Wars supporting EvidenceBinding count must be 3'; END IF;
END $$;

COMMIT;