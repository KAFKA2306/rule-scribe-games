BEGIN;

-- Canonical scope: Arclight Japanese Magnolia base game released 2021-03-11.
-- Additional objective cards, variants, unofficial summaries, and later interpretations remain separate.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'publisher:arclight:magnolia:2021-product',
  'https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/',
  'マグノリア — Arclight product page',
  'publisher_product_page','Arclight','physical','ja','2021-03-11 Japanese edition',
  '{"authority":"official_japanese_product_page","audit_date":"2026-08-26","scope":"identity_round_structure_core_actions_end_scoring"}'::jsonb
),
(
  'publisher:arclight:magnolia:2021-faq',
  'https://arclightgames.jp/%E3%80%90faq%E3%80%91%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/',
  'マグノリア — Arclight FAQ',
  'publisher_faq','Arclight','physical','ja','2021-03-26 FAQ',
  '{"authority":"official_japanese_faq","audit_date":"2026-08-26","scope":"draw_phase_clarifications"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('magnolia:2021:identity','publisher:arclight:magnolia:2021-product','商品概要','2021-03-11; 2–5 players; 10–20 min; age 10+'),
('magnolia:2021:round','publisher:arclight:magnolia:2021-product','ゲームの概要','about 4–5 rounds; six phases per round'),
('magnolia:2021:draw','publisher:arclight:magnolia:2021-product','1.ドローフェイズ','discard any number; draw until hand reaches five'),
('magnolia:2021:draw-faq','publisher:arclight:magnolia:2021-faq','ドローフェイズ','exchange may be used once per draw phase; no prefill before choosing discards'),
('magnolia:2021:placement','publisher:arclight:magnolia:2021-product','2.配置フェイズ','choose 2 coins, 1 coin + play 1, or play 2; pay card costs'),
('magnolia:2021:line-bonus','publisher:arclight:magnolia:2021-product','2.配置フェイズ','same race or profession across a row/column triggers its bonus'),
('magnolia:2021:war','publisher:arclight:magnolia:2021-product','3.戦争フェイズ','sum strength of front card in each vertical column; award VP by rank'),
('magnolia:2021:development','publisher:arclight:magnolia:2021-product','4.発展フェイズ','units advance civilization'),
('magnolia:2021:income','publisher:arclight:magnolia:2021-product','5.収入フェイズ','units generate money'),
('magnolia:2021:vp','publisher:arclight:magnolia:2021-product','6.VPフェイズ','units generate VP'),
('magnolia:2021:end','publisher:arclight:magnolia:2021-product','ゲームの終了条件','end after VP phase if anyone has 40 VP or nine units'),
('magnolia:2021:scoring','publisher:arclight:magnolia:2021-product','ゲームの終了条件','convert remaining money to VP; rank by total VP')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='magnolia' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'Magnolia row absent; skipping catalog-bound seed'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required'; END IF;

  UPDATE public.games SET
    title='マグノリア',title_ja='マグノリア',title_en='Magnolia',
    description='3×3の王国にユニットカードを配置し、種族・職業の並びによるボーナスや戦争、発展、収入を通じてVPを競うカードゲーム。',
    summary='各ラウンドはドロー、配置、戦争、発展、収入、VPの6フェイズで進み、40VP到達または9体配置が終了条件になる。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/',
    source_url='https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/',
    official_url='https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='マグノリア（2021年3月11日）',language_code='ja',publisher='Arclight',
    source_revision='Arclight 2021 product page + official FAQ; audited 2026-08-26',
    min_players=2,max_players=5,play_time=20,min_age=10,published_year=2021,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='マグノリア（2021年3月11日）'
    AND COALESCE(platform,'')='physical' AND COALESCE(revision_label,'')='arclight-2021-ja-product-faq'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,revision_label,platform,publisher_name,status,verification_status,source_ids)
    VALUES(v_game_id,v_work_id,1,'1.0','ja','マグノリア（2021年3月11日）',
      'Arclight 2021 product page + official FAQ; audited 2026-08-26',true,
      'arclight-2021-ja-product-faq','physical','Arclight','active','source_bound',
      ARRAY['publisher:arclight:magnolia:2021-product','publisher:arclight:magnolia:2021-faq']::text[])
    RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='Arclight 2021 product page + official FAQ; audited 2026-08-26',
      source_ids=ARRAY['publisher:arclight:magnolia:2021-product','publisher:arclight:magnolia:2021-faq']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'round.structure','turn','ゲームはおおむね4～5ラウンドで進み、各ラウンドはドロー、配置、戦争、発展、収入、VPの6フェイズで構成される。',10,'source_bound','magnolia:rule:round.structure','magnolia:binding:round.structure','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:round','{}'::jsonb),
  (v_ruleset_id,'phase.draw','action','ドローフェイズでは手札から好きな枚数を捨て、手札が5枚になるまでカードを引く。',20,'source_bound','magnolia:rule:phase.draw','magnolia:binding:phase.draw','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:draw','{}'::jsonb),
  (v_ruleset_id,'phase.draw.once','condition','手札を捨てて5枚まで引く処理は1回のドローフェイズにつき1度だけ。前ラウンドから手札が5枚未満でも、先に5枚へ補充せず持ち越した手札から捨てるカードを選ぶ。',30,'source_bound','magnolia:rule:phase.draw.once','magnolia:binding:phase.draw.once','https://arclightgames.jp/%E3%80%90faq%E3%80%91%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:draw-faq','{}'::jsonb),
  (v_ruleset_id,'phase.placement','action','配置フェイズでは「2金を得る」「1金を得てカード1枚を配置する」「カード2枚を配置する」のいずれかを選び、配置するカードのコストを支払う。',40,'source_bound','magnolia:rule:phase.placement','magnolia:binding:phase.placement','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:placement','{}'::jsonb),
  (v_ruleset_id,'placement.line_bonus','effect','3×3の王国で縦または横一列に同じ種族または同じ職業が揃うと、その種族・職業のボーナスが発生する。',50,'source_bound','magnolia:rule:placement.line_bonus','magnolia:binding:placement.line_bonus','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:line-bonus','{}'::jsonb),
  (v_ruleset_id,'phase.war','action','戦争フェイズでは各縦列の一番前のカードの戦力を合計し、合計戦力が高いプレイヤーから順に戦争によるVPを得る。',60,'source_bound','magnolia:rule:phase.war','magnolia:binding:phase.war','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:war','{}'::jsonb),
  (v_ruleset_id,'phase.development','action','発展フェイズでは、自分のユニットによる文明の発展効果を処理する。',70,'source_bound','magnolia:rule:phase.development','magnolia:binding:phase.development','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:development','{}'::jsonb),
  (v_ruleset_id,'phase.income','action','収入フェイズでは、自分のユニットによる収入を処理してお金を得る。',80,'source_bound','magnolia:rule:phase.income','magnolia:binding:phase.income','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:income','{}'::jsonb),
  (v_ruleset_id,'phase.vp','action','VPフェイズでは、自分のユニットによるVP獲得を処理する。',90,'source_bound','magnolia:rule:phase.vp','magnolia:binding:phase.vp','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:vp','{}'::jsonb),
  (v_ruleset_id,'end.trigger','round_end','VPフェイズ終了時に誰かが40VP以上を持つか、誰かが場に9体のユニットを配置していればゲーム終了。どちらも満たさなければ次ラウンドのドローフェイズへ進む。',100,'source_bound','magnolia:rule:end.trigger','magnolia:binding:end.trigger','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:end','{}'::jsonb),
  (v_ruleset_id,'victory.scoring','victory','ゲーム終了後、残ったお金をVPへ変換し、最もVPが多いプレイヤーが1位となる。',110,'source_bound','magnolia:rule:victory.scoring','magnolia:binding:victory.scoring','https://arclightgames.jp/product/%E3%83%9E%E3%82%B0%E3%83%8E%E3%83%AA%E3%82%A2/','magnolia:2021:scoring','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'magnolia:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"official_source_normalization","audit_date":"2026-08-26","scope":"arclight_2021_ja_base"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'magnolia:binding:'||rn.rule_id,'magnolia:rule:'||rn.rule_id,
    CASE WHEN rn.rule_id='phase.draw.once' THEN 'publisher:arclight:magnolia:2021-faq' ELSE 'publisher:arclight:magnolia:2021-product' END,
    rn.source_locator,'supports','{"review":"official_publisher_source"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 11 THEN RAISE EXCEPTION 'Magnolia RuleNode count must be 11'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 11 THEN RAISE EXCEPTION 'Magnolia Claim count must be 11'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 11 THEN RAISE EXCEPTION 'Magnolia EvidenceBinding count must be 11'; END IF;
END $$;

COMMIT;