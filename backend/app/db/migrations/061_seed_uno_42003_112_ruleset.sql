BEGIN;

-- Canonical scope: Mattel UNO Card Game product #42003, 112-card customizable-Wild revision.
-- Older 108-card instruction sheets and other UNO variants are excluded from this RuleSet.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:mattel:uno:42003-product','https://shop.mattel.com/products/uno-card-game-42003','UNO Card Game — Mattel Product #42003','publisher_product_page','Mattel','physical','en','current-112-card-product','{"authority":"publisher","audit_date":"2026-08-25","scope":"product_42003_identity_112_cards"}'::jsonb),
('publisher:mattel:uno:42003-rules-2015','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','UNO Card Game — Mattel instruction sheet 42003-0970-G1','publisher_rulebook','Mattel','physical','en','42003-0970-G1-2015','{"authority":"publisher","audit_date":"2026-08-25","scope":"product_42003_112_card_rules","copyright":"2015"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('uno42003:product:identity','publisher:mattel:uno:42003-product',NULL,'UNO','product #42003; 112 cards; 2–10 players; ages 7+; three blank customizable Wild cards'),
('uno42003:rules:contents','publisher:mattel:uno:42003-rules-2015',1,'Contents','112 cards including Wild Swap Hands and three Wild Customizable cards'),
('uno42003:rules:setup','publisher:mattel:uno:42003-rules-2015',1,'Setup','highest-number dealer; seven cards each; draw and discard piles'),
('uno42003:rules:turn','publisher:mattel:uno:42003-rules-2015',1,'Let’s Play','match number, color or symbol; Wild alternative; draw rules'),
('uno42003:rules:draw-two','publisher:mattel:uno:42003-rules-2015',2,'Functions of Action Cards','Draw Two effect and opening-card behavior'),
('uno42003:rules:reverse','publisher:mattel:uno:42003-rules-2015',2,'Functions of Action Cards','Reverse effect and opening-card behavior'),
('uno42003:rules:skip','publisher:mattel:uno:42003-rules-2015',2,'Functions of Action Cards','Skip effect and opening-card behavior'),
('uno42003:rules:wild','publisher:mattel:uno:42003-rules-2015',2,'Functions of Action Cards','Wild color choice and opening-card behavior'),
('uno42003:rules:wild-draw-four','publisher:mattel:uno:42003-rules-2015',2,'Functions of Action Cards','Wild Draw Four play restriction, challenge and penalties'),
('uno42003:rules:swap-hands','publisher:mattel:uno:42003-rules-2015',2,'Functions of Action Cards','Wild Swap Hands effect'),
('uno42003:rules:customizable','publisher:mattel:uno:42003-rules-2015',2,'Wild Customizable card','house-rule cards are optional; classic game removes all four extra Wild cards'),
('uno42003:rules:uno-call','publisher:mattel:uno:42003-rules-2015',3,'Going Out','call UNO on next-to-last card; two-card penalty if caught in time'),
('uno42003:rules:round-end','publisher:mattel:uno:42003-rules-2015',3,'Going Out','round ends when a player has no cards; draw-pile depletion reshuffles discard pile'),
('uno42003:rules:scoring','publisher:mattel:uno:42003-rules-2015',3,'Scoring','winner scores opponents remaining cards; action-card point values'),
('uno42003:rules:win','publisher:mattel:uno:42003-rules-2015',4,'Winning the Game','first player to 500 points wins')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='uno' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'UNO canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical UNO Work row is required'; END IF;

  UPDATE public.games SET
    title='UNO',title_ja='ウノ',title_en='UNO',
    description='場札と同じ色・数字・記号のカードを出して手札をなくし、ラウンドごとの得点を積み上げて500点を目指すカードゲーム。',
    summary='各手番で場札と色・数字・記号が一致するカードかワイルドを1枚出す。出せなければ1枚引く。残り1枚でUNOと宣言し、先に手札をなくしたプレイヤーが相手の残り札から得点する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://shop.mattel.com/products/uno-card-game-42003',
    source_url='https://service.mattel.com/instruction_sheets/41940-Wild.pdf',
    official_url='https://shop.mattel.com/products/uno-card-game-42003',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='UNO Card Game Product #42003（112枚・Customizable Wild Cards）',language_code='ja',publisher='Mattel',
    source_revision='Mattel Product #42003 current 112-card product; instruction sheet 42003-0970-G1 ©2015; older 108-card instructions and other UNO variants excluded; audited 2026-08-25',
    min_players=2,max_players=10,play_time=30,min_age=7,published_year=1995,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='UNO Card Game Product #42003（112枚・Customizable Wild Cards）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='42003-0970-G1-2015'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','UNO Card Game Product #42003（112枚・Customizable Wild Cards）',
      'Mattel Product #42003 current 112-card product; instruction sheet 42003-0970-G1 ©2015; older 108-card instructions and other UNO variants excluded; audited 2026-08-25',
      true,'42003-0970-G1-2015','physical','Mattel','active','source_bound',
      ARRAY['publisher:mattel:uno:42003-product','publisher:mattel:uno:42003-rules-2015']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Mattel Product #42003 current 112-card product; instruction sheet 42003-0970-G1 ©2015; older 108-card instructions and other UNO variants excluded; audited 2026-08-25',
      publisher_name='Mattel',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:mattel:uno:42003-product','publisher:mattel:uno:42003-rules-2015']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.base','setup','各プレイヤーが1枚引き、数字が最も大きいプレイヤーがディーラーになる。ディーラーは各プレイヤーに7枚ずつ配り、残りを山札にして一番上を表向きにし、捨て札置き場を作る。',10,'source_bound','uno42003:rule:setup.base','uno42003:binding:setup.base','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:setup','{}'::jsonb),
  (v_ruleset_id,'turn.match','turn','ディーラーの左隣から始め、手番では捨て札の一番上と数字・色・記号のいずれかが一致するカードを1枚出すか、ワイルドカードを出す。',20,'source_bound','uno42003:rule:turn.match','uno42003:binding:turn.match','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:turn','{}'::jsonb),
  (v_ruleset_id,'turn.draw','turn','出せるカードがない場合は山札から1枚引き、そのカードが出せれば同じ手番で出せる。出せる手札があっても出さずに1枚引くことを選べるが、その場合は引いたカード以外を続けて出せない。',30,'source_bound','uno42003:rule:turn.draw','uno42003:binding:turn.draw','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:turn','{}'::jsonb),
  (v_ruleset_id,'action.draw-two','effect','ドロー2を出すと次のプレイヤーは2枚引いて手番を失う。',40,'source_bound','uno42003:rule:action.draw-two','uno42003:binding:action.draw-two','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:draw-two','{}'::jsonb),
  (v_ruleset_id,'action.reverse','effect','リバースを出すと進行方向が逆になる。',50,'source_bound','uno42003:rule:action.reverse','uno42003:binding:action.reverse','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:reverse','{}'::jsonb),
  (v_ruleset_id,'action.skip','effect','スキップを出すと次のプレイヤーは手番を失う。',60,'source_bound','uno42003:rule:action.skip','uno42003:binding:action.skip','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:skip','{}'::jsonb),
  (v_ruleset_id,'action.wild','effect','ワイルドは他に出せるカードがあっても出すことができ、出したプレイヤーが次に続く色を指定する。',70,'source_bound','uno42003:rule:action.wild','uno42003:binding:action.wild','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:wild','{}'::jsonb),
  (v_ruleset_id,'action.wild-draw-four','condition','ワイルドドロー4は捨て札と同じ色のカードを手札に持っていない場合だけ出せる。次のプレイヤーは4枚引いて手番を失い、疑わしい場合はチャレンジできる。不正なら出した側が4枚、正当ならチャレンジ側が合計6枚引く。',80,'source_bound','uno42003:rule:action.wild-draw-four','uno42003:binding:action.wild-draw-four','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:wild-draw-four','{}'::jsonb),
  (v_ruleset_id,'action.swap-hands','effect','ワイルド・スワップ・ハンズを出したプレイヤーは任意の相手1人と手札をすべて交換し、続く色を指定する。',90,'source_bound','uno42003:rule:action.swap-hands','uno42003:binding:action.swap-hands','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:swap-hands','{}'::jsonb),
  (v_ruleset_id,'variant.customizable-wild','condition','カスタマイズ可能なワイルドはゲーム前に合意したハウスルールを書いて1～3枚使える。クラシックUNOとして遊ぶ場合は、ワイルド・スワップ・ハンズ1枚とカスタマイズ可能なワイルド3枚をデッキから除く。',100,'source_bound','uno42003:rule:variant.customizable-wild','uno42003:binding:variant.customizable-wild','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:customizable','{}'::jsonb),
  (v_ruleset_id,'round.uno-call','condition','残り2枚から1枚を出して手札が1枚になるときは「UNO」と宣言する。宣言せず、次のプレイヤーが手番を始める前に指摘された場合は2枚引く。',110,'source_bound','uno42003:rule:round.uno-call','uno42003:binding:round.uno-call','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:uno-call','{}'::jsonb),
  (v_ruleset_id,'round.end','round_end','誰かの手札が0枚になったらラウンド終了。山札が尽きても誰も上がっていない場合は捨て札をシャッフルして新しい山札にし、プレイを続ける。',120,'source_bound','uno42003:rule:round.end','uno42003:binding:round.end','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:round-end','{}'::jsonb),
  (v_ruleset_id,'score.round','scoring','ラウンドで最初に手札をなくしたプレイヤーは、相手の残り札を得点する。数字カードは額面、ドロー2・リバース・スキップは各20点、ワイルドとワイルドドロー4は各50点、ワイルド・スワップ・ハンズとカスタマイズ可能なワイルドは各40点。',130,'source_bound','uno42003:rule:score.round','uno42003:binding:score.round','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:scoring','{}'::jsonb),
  (v_ruleset_id,'game.win','victory','ラウンド得点を累積し、最初に500点へ到達したプレイヤーがゲームに勝つ。',140,'source_bound','uno42003:rule:game.win','uno42003:binding:game.win','https://service.mattel.com/instruction_sheets/41940-Wild.pdf','uno42003:rules:win','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'uno42003:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-25","scope":"uno_42003_112_card_revision"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT
    'uno42003:binding:'||rn.rule_id,
    'uno42003:rule:'||rn.rule_id,
    'publisher:mattel:uno:42003-rules-2015',
    rn.source_locator,
    'supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 14 THEN RAISE EXCEPTION 'UNO 42003 source-bound RuleNode count must be 14'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 14 THEN RAISE EXCEPTION 'UNO 42003 accepted Claim count must be 14'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 14 THEN RAISE EXCEPTION 'UNO 42003 supporting EvidenceBinding count must be 14'; END IF;
END $$;

COMMIT;
