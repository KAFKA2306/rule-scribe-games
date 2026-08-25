BEGIN;

-- Canonical scope: Asmadi Games base game "We Didn't Playtest This At All" (ASI-0003).
-- "We Didn't Playtest This Either", Legacies, Pasted-On Theme and other Playtest decks remain separate products/revisions.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'publisher:asmadi:playtest:asi-0003-catalog',
  'https://asmadigames.com/AsmadiCatalog.pdf',
  'We Didn''t Playtest This At All — Asmadi Games catalog (ASI-0003)',
  'publisher_catalog','Asmadi Games','physical','en','ASI-0003',
  '{"authority":"publisher_catalog","audit_date":"2026-08-26","scope":"base_product_identity_players_time_product_family_boundary"}'::jsonb
),
(
  'publisher:asmadi:playtest:base-rulebook',
  'https://www.asmadigames.com/rules/Playtest_Rules.pdf',
  'We Didn''t Playtest This at All! — official rules',
  'publisher_rulebook','Asmadi Games','physical','en','Playtest_Rules',
  '{"authority":"publisher_rulebook","audit_date":"2026-08-26","scope":"objective_setup_turn_sequence_card_instructions"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('playtest:catalog:identity','publisher:asmadi:playtest:asi-0003-catalog',1,'WE DIDN''T PLAYTEST THIS AT ALL','ASI-0003; 2-10 players; 1-5 mins; separate from Either, Legacies and Pasted-On Theme'),
('playtest:rules:objective','publisher:asmadi:playtest:base-rulebook',1,'The Rules','If everyone except you has lost, you win'),
('playtest:rules:setup','publisher:asmadi:playtest:base-rulebook',1,'The Rules','Shuffle all cards; deal two to each player; choose a first player randomly'),
('playtest:rules:turn','publisher:asmadi:playtest:base-rulebook',1,'The Rules','Draw one card, then play one card and follow its instructions'),
('playtest:rules:pass','publisher:asmadi:playtest:base-rulebook',1,'The Rules','After the turn, play passes to the player on the left')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='we-didnt-playtest-this-at-all' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'We Didn''t Playtest This At All row absent; skipping catalog-bound seed'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required'; END IF;

  UPDATE public.games SET
    title_en='We Didn''t Playtest This At All',
    description='カードに書かれた指示そのものが展開を決める、短時間のパーティーカードゲーム。',
    summary='2枚の手札で開始し、手番では1枚引いて1枚プレイする。カードの指示によって勝敗が決まる。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://asmadigames.com/AsmadiCatalog.pdf',
    source_url='https://www.asmadigames.com/rules/Playtest_Rules.pdf',official_url='https://asmadigames.com/AsmadiCatalog.pdf',
    source_trust='official_publisher',content_review_status='human_reviewed',is_official=true,
    edition_label='Asmadi Games base game / ASI-0003',publisher='Asmadi Games',
    source_revision='Asmadi Games ASI-0003 catalog + Playtest_Rules.pdf; audited 2026-08-26',
    min_players=2,max_players=10,play_time=5,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Asmadi Games base game / ASI-0003'
    AND COALESCE(platform,'')='physical' AND COALESCE(revision_label,'')='asmadi-asi-0003-base'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,revision_label,platform,publisher_name,status,verification_status,source_ids)
    VALUES(v_game_id,v_work_id,1,'1.0','ja','Asmadi Games base game / ASI-0003',
      'Asmadi Games ASI-0003 catalog + Playtest_Rules.pdf; audited 2026-08-26',true,
      'asmadi-asi-0003-base','physical','Asmadi Games','active','source_bound',
      ARRAY['publisher:asmadi:playtest:asi-0003-catalog','publisher:asmadi:playtest:base-rulebook']::text[])
    RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='Asmadi Games ASI-0003 catalog + Playtest_Rules.pdf; audited 2026-08-26',
      source_ids=ARRAY['publisher:asmadi:playtest:asi-0003-catalog','publisher:asmadi:playtest:base-rulebook']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'objective.last_player','victory','自分以外の全員が敗北した時点で、そのプレイヤーが勝者になる。',10,'source_bound','playtest:rule:objective.last_player','playtest:binding:objective.last_player','https://www.asmadigames.com/rules/Playtest_Rules.pdf','playtest:rules:objective','{}'::jsonb),
  (v_ruleset_id,'setup.base','setup','すべてのカードを混ぜ、各プレイヤーに2枚ずつ配り、最初のプレイヤーを無作為に決める。',20,'source_bound','playtest:rule:setup.base','playtest:binding:setup.base','https://www.asmadigames.com/rules/Playtest_Rules.pdf','playtest:rules:setup','{}'::jsonb),
  (v_ruleset_id,'turn.draw_play','turn','自分の手番では山札から1枚引き、その後手札から1枚をプレイして、そのカードに書かれた指示に従う。',30,'source_bound','playtest:rule:turn.draw_play','playtest:binding:turn.draw_play','https://www.asmadigames.com/rules/Playtest_Rules.pdf','playtest:rules:turn','{}'::jsonb),
  (v_ruleset_id,'turn.pass_left','turn','手番の処理が終わったら、左隣のプレイヤーへ手番を移す。',40,'source_bound','playtest:rule:turn.pass_left','playtest:binding:turn.pass_left','https://www.asmadigames.com/rules/Playtest_Rules.pdf','playtest:rules:pass','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'playtest:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-26","scope":"asmadi_asi_0003_base"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'playtest:binding:'||rn.rule_id,'playtest:rule:'||rn.rule_id,'publisher:asmadi:playtest:base-rulebook',rn.source_locator,'supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 4 THEN RAISE EXCEPTION 'Playtest RuleNode count must be 4'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 4 THEN RAISE EXCEPTION 'Playtest Claim count must be 4'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 4 THEN RAISE EXCEPTION 'Playtest EvidenceBinding count must be 4'; END IF;
END $$;

COMMIT;
