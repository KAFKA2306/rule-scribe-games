BEGIN;

-- Canonical scope: current AMIGO Bohnanza base game, Art.Nr.01661.
-- Expansion Set, 25 Jahre-Edition, Das Duell, dice game, Dahlia and other Bohnanza products remain separate products/revisions.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES (
  'publisher:amigo:bohnanza:01661-product',
  'https://www.amigo-spiele.de/bohnanza_1661_1075',
  'Bohnanza — AMIGO base game product page (Art.Nr.01661)',
  'publisher_product_page','AMIGO Spiel + Freizeit','physical','de','Art.Nr.01661',
  '{"authority":"publisher_product_page","audit_date":"2026-08-26","scope":"base_identity_setup_turn_phases_harvest_end"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('bohnanza:01661:setup-fields','publisher:amigo:bohnanza:01661-product','Spielablauf','Each player gets a beanfield mat; starting player gets the start card'),
('bohnanza:01661:setup-hand','publisher:amigo:bohnanza:01661-product','Spielablauf','Shuffle all cards; deal five cards each; hand order may not change'),
('bohnanza:01661:turn-four-phases','publisher:amigo:bohnanza:01661-product','Spielablauf','Active player turn consists of four phases'),
('bohnanza:01661:phase-one','publisher:amigo:bohnanza:01661-product','Spielablauf','Plant front bean card; optionally second; one bean type per field'),
('bohnanza:01661:phase-two','publisher:amigo:bohnanza:01661-product','Spielablauf','Reveal two bean cards and trade using revealed cards and hand cards'),
('bohnanza:01661:phase-three','publisher:amigo:bohnanza:01661-product','Spielablauf','All players plant traded or revealed bean cards'),
('bohnanza:01661:phase-four','publisher:amigo:bohnanza:01661-product','Spielablauf','Draw three cards'),
('bohnanza:01661:harvest','publisher:amigo:bohnanza:01661-product','Spielablauf','Fields may be harvested at any time; beanometer determines bean dollars'),
('bohnanza:01661:end','publisher:amigo:bohnanza:01661-product','Spielablauf','Game ends when draw pile is exhausted for the third time; most bean dollars wins')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='bohnanza' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'Bohnanza row absent; skipping catalog-bound seed'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required'; END IF;

  UPDATE public.games SET
    title_en='Bohnanza',
    description='豆カードの手札順を保ったまま、植え付け・交渉・収穫を繰り返して豆ターラーを集めるカードゲーム。',
    summary='手札の順番を変えず、4フェイズで植える・取引する・植える・補充する。山札が3回尽きたら最も多くの豆ターラーを持つプレイヤーが勝つ。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://www.amigo-spiele.de/bohnanza_1661_1075',
    source_url='https://www.amigo-spiele.de/bohnanza_1661_1075',official_url='https://www.amigo-spiele.de/bohnanza_1661_1075',
    source_trust='official_publisher',content_review_status='human_reviewed',is_official=true,
    edition_label='AMIGO base game / Art.Nr.01661',publisher='AMIGO Spiel + Freizeit',
    source_revision='AMIGO Art.Nr.01661 product page; audited 2026-08-26',
    min_players=3,max_players=5,play_time=45,min_age=10,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='AMIGO base game / Art.Nr.01661'
    AND COALESCE(platform,'')='physical' AND COALESCE(revision_label,'')='amigo-01661-current-base'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,revision_label,platform,publisher_name,status,verification_status,source_ids)
    VALUES(v_game_id,v_work_id,1,'1.0','ja','AMIGO base game / Art.Nr.01661',
      'AMIGO Art.Nr.01661 product page; audited 2026-08-26',true,
      'amigo-01661-current-base','physical','AMIGO Spiel + Freizeit','active','source_bound',
      ARRAY['publisher:amigo:bohnanza:01661-product']::text[])
    RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='AMIGO Art.Nr.01661 product page; audited 2026-08-26',
      source_ids=ARRAY['publisher:amigo:bohnanza:01661-product']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'setup.fields','setup','各プレイヤーは豆畑ボードを受け取り、最初のプレイヤーはスタートカードも受け取る。',10,'source_bound','bohnanza:rule:setup.fields','bohnanza:binding:setup.fields','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:setup-fields','{}'::jsonb),
  (v_ruleset_id,'setup.hand','setup','すべてのカードを混ぜて各プレイヤーに5枚ずつ配る。ゲーム中、手札のカード順を変えてはいけない。',20,'source_bound','bohnanza:rule:setup.hand','bohnanza:binding:setup.hand','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:setup-hand','{}'::jsonb),
  (v_ruleset_id,'turn.four_phases','turn','手番は4つのフェイズを順番に行う。',30,'source_bound','bohnanza:rule:turn.four_phases','bohnanza:binding:turn.four_phases','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:turn-four-phases','{}'::jsonb),
  (v_ruleset_id,'turn.phase_one','turn','第1フェイズでは手札の一番前の豆カードを必ず畑に植え、任意で2枚目も植えられる。1つの畑には1種類の豆だけを植える。',40,'source_bound','bohnanza:rule:turn.phase_one','bohnanza:binding:turn.phase_one','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:phase-one','{}'::jsonb),
  (v_ruleset_id,'turn.phase_two','turn','第2フェイズでは山札から豆カード2枚を表向きにし、それらと自分の手札を使って他のプレイヤーと取引する。',50,'source_bound','bohnanza:rule:turn.phase_two','bohnanza:binding:turn.phase_two','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:phase-two','{}'::jsonb),
  (v_ruleset_id,'turn.phase_three','turn','第3フェイズでは、取引したカードや表向きにしたカードを各プレイヤーが自分の豆畑へ植える。',60,'source_bound','bohnanza:rule:turn.phase_three','bohnanza:binding:turn.phase_three','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:phase-three','{}'::jsonb),
  (v_ruleset_id,'turn.phase_four','turn','第4フェイズでは山札から3枚のカードを引く。',70,'source_bound','bohnanza:rule:turn.phase_four','bohnanza:binding:turn.phase_four','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:phase-four','{}'::jsonb),
  (v_ruleset_id,'harvest.beanometer','effect','豆畑はいつでも収穫でき、得られる豆ターラーの数はその畑の豆の枚数とカードのボーノメーターで決まる。',80,'source_bound','bohnanza:rule:harvest.beanometer','bohnanza:binding:harvest.beanometer','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:harvest','{}'::jsonb),
  (v_ruleset_id,'end.third_deck','victory','山札が3回目に尽きるとゲーム終了となり、最も多くの豆ターラーを持つプレイヤーが勝つ。',90,'source_bound','bohnanza:rule:end.third_deck','bohnanza:binding:end.third_deck','https://www.amigo-spiele.de/bohnanza_1661_1075','bohnanza:01661:end','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'bohnanza:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_product_page_normalization","audit_date":"2026-08-26","scope":"amigo_01661_base"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'bohnanza:binding:'||rn.rule_id,'bohnanza:rule:'||rn.rule_id,'publisher:amigo:bohnanza:01661-product',rn.source_locator,'supports','{"review":"publisher_product_page"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 9 THEN RAISE EXCEPTION 'Bohnanza RuleNode count must be 9'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 9 THEN RAISE EXCEPTION 'Bohnanza Claim count must be 9'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 9 THEN RAISE EXCEPTION 'Bohnanza EvidenceBinding count must be 9'; END IF;
END $$;

COMMIT;
