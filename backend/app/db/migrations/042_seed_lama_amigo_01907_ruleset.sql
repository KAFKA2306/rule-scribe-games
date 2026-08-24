BEGIN;

-- Canonical scope: AMIGO LAMA card game, Art.Nr. 01907, Rules Version 1.1 (2019).
-- LAMA Party, LAMA Dice, LAMA Kadabra, digital implementations, and house rules are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:amigo:lama:rules-v1.1-en','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','LAMA — English Rules Version 1.1','publisher_rulebook','AMIGO Spiel + Freizeit GmbH','physical','en','version-1.1-2019','{"authority":"publisher","audit_date":"2026-08-24","scope":"lama_art_nr_01907_base_game"}'::jsonb),
('publisher:amigo:lama:rules-index','https://blog.amigo-spiele.de/spielregeln/','AMIGO rules index — LAMA Art.Nr.01907','publisher_product_page','AMIGO Spiel + Freizeit GmbH','physical','de','current-rules-index','{"authority":"publisher","audit_date":"2026-08-24","scope":"product_identity_and_variant_boundary"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('lama:rules:setup','publisher:amigo:lama:rules-v1.1-en',1,'Setting Up the Game','deal six cards to each player; remaining cards form draw pile; turn over top card for discard pile'),
('lama:rules:turn','publisher:amigo:lama:rules-v1.1-en',1,'Playing the Game','choose exactly one action: play a card, draw a card, or quit'),
('lama:rules:play','publisher:amigo:lama:rules-v1.1-en',1,'Playing a Card','same value or exactly one higher; llama follows 6 or llama; llama or 1 follows llama'),
('lama:rules:draw','publisher:amigo:lama:rules-v1.1-en',1,'Drawing a Card','draw one and end turn; exhausted draw pile is not rebuilt'),
('lama:rules:quit','publisher:amigo:lama:rules-v1.1-en',1,'Quitting','leave the current round and place remaining cards face down'),
('lama:rules:round-end','publisher:amigo:lama:rules-v1.1-en',2,'The End of a Round','round ends when one player empties hand or all players quit; lone remaining player cannot draw'),
('lama:rules:scoring','publisher:amigo:lama:rules-v1.1-en',2,'Scoring','remaining numeric values count once per distinct value; llamas total 10 points'),
('lama:rules:return-token','publisher:amigo:lama:rules-v1.1-en',2,'Returning Tokens','a player who empties hand may return one 1-point or 10-point token'),
('lama:rules:game-end','publisher:amigo:lama:rules-v1.1-en',2,'The End of the Game','game ends once someone has 40 or more points; fewest points wins; ties share victory')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='l-l-a-m-a' LIMIT 1;
  -- The shared CI fixture may not yet contain every catalog game. Production must contain the canonical row.
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'LAMA canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical LAMA Work row is required'; END IF;

  UPDATE public.games SET
    title='LAMA',title_ja='ラマ',title_en='LAMA',
    description='手札を出し切ってマイナス点を避ける、ライナー・クニツィア作のカードゲーム。出せない、または出したくないときは、カードを引くかそのラウンドから降りるかを選ぶ。',
    summary='同じ数字か1つ大きい数字を出し、手札を減らす。出せないときは引くか降りるかを選び、40点以上のマイナス点が発生したラウンドでゲーム終了。最少失点が勝つ。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://blog.amigo-spiele.de/spielregeln/',
    source_url='https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf',
    official_url='https://blog.amigo-spiele.de/spielregeln/',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='LAMA（AMIGO Art.Nr.01907）',language_code='ja',publisher='AMIGO Spiel + Freizeit GmbH',
    source_revision='AMIGO LAMA Art.Nr.01907, English Rules Version 1.1 (2019); Party/Dice/Kadabra excluded; audited 2026-08-24',
    min_players=2,max_players=6,play_time=20,min_age=8,published_year=2019,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='LAMA（AMIGO Art.Nr.01907）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='amigo-01907-v1.1-2019-en'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','LAMA（AMIGO Art.Nr.01907）',
      'AMIGO LAMA Art.Nr.01907, English Rules Version 1.1 (2019); Party/Dice/Kadabra excluded; audited 2026-08-24',
      true,'amigo-01907-v1.1-2019-en','physical','AMIGO Spiel + Freizeit GmbH','active','source_bound',
      ARRAY['publisher:amigo:lama:rules-v1.1-en','publisher:amigo:lama:rules-index']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',
      source_revision='AMIGO LAMA Art.Nr.01907, English Rules Version 1.1 (2019); Party/Dice/Kadabra excluded; audited 2026-08-24',
      is_active=true,publisher_name='AMIGO Spiel + Freizeit GmbH',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:amigo:lama:rules-v1.1-en','publisher:amigo:lama:rules-index']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.base','setup','カードをすべて混ぜ、各プレイヤーに6枚ずつ配る。残りを裏向きの山札にし、一番上の1枚を表向きにして捨て札置き場を作る。得点チップを全員が取れる場所に置く。',10,'source_bound','lama:rule:setup.base','lama:binding:setup.base','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:setup','{}'::jsonb),
  (v_ruleset_id,'turn.choice','turn','手番では「カードを1枚出す」「カードを1枚引く」「そのラウンドから降りる」の3つから1つを選び、実行後は次のプレイヤーへ手番を移す。',20,'source_bound','lama:rule:turn.choice','lama:binding:turn.choice','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:turn','{}'::jsonb),
  (v_ruleset_id,'action.play-card','action','捨て札の一番上と同じ数字、またはちょうど1大きい数字を出せる。6の上には6かラマ、ラマの上にはラマか1を出せる。',30,'source_bound','lama:rule:action.play-card','lama:binding:action.play-card','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:play','{}'::jsonb),
  (v_ruleset_id,'action.draw','action','山札から1枚引いたら、その手番ではカードを出さず次のプレイヤーへ移る。山札が尽きても捨て札を山札に戻さず、それ以降は「引く」を選べない。',40,'source_bound','lama:rule:action.draw','lama:binding:action.draw','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:draw','{}'::jsonb),
  (v_ruleset_id,'action.quit','action','カードを出さず、引くこともしない場合は現在のラウンドから降り、残りの手札を裏向きで自分の前に置く。そのラウンドには戻らない。',50,'source_bound','lama:rule:action.quit','lama:binding:action.quit','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:quit','{}'::jsonb),
  (v_ruleset_id,'round.end','condition','誰か1人が手札をすべて出すか、全員がラウンドから降りたら、そのラウンドは直ちに終了する。1人だけ残った場合、そのプレイヤーは続行できるがカードは引けない。',60,'source_bound','lama:rule:round.end','lama:binding:round.end','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:round-end','{}'::jsonb),
  (v_ruleset_id,'round.scoring','scoring','ラウンド終了時、残った数字カードは数字ごとに1回だけその値をマイナス点として数え、ラマは何枚残っていても合計10点として数える。得たマイナス点と同額の得点チップを受け取る。',70,'source_bound','lama:rule:round.scoring','lama:binding:round.scoring','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:scoring','{}'::jsonb),
  (v_ruleset_id,'round.return-token','scoring','手札をすべて出し切ったプレイヤーが以前から得点チップを持っている場合、1点チップまたは10点チップのどちらか1枚を選んで返せる。',80,'source_bound','lama:rule:round.return-token','lama:binding:round.return-token','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:return-token','{}'::jsonb),
  (v_ruleset_id,'game.end','game_end','誰かの累積マイナス点が40点以上になったラウンドでゲームを終了する。累積マイナス点が最も少ないプレイヤーが勝ち、同点なら同点者全員が勝利する。',90,'source_bound','lama:rule:game.end','lama:binding:game.end','https://blog.amigo-spiele.de/content/ap/rule/01907-GB-AmigoRule.pdf','lama:rules:game-end','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'lama:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"amigo_lama_01907_v1_1"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'lama:binding:'||rn.rule_id,'lama:rule:'||rn.rule_id,'publisher:amigo:lama:rules-v1.1-en',rn.source_locator,'supports',
    '{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 9 THEN
    RAISE EXCEPTION 'LAMA source-bound RuleNode count must be 9';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 9 THEN
    RAISE EXCEPTION 'LAMA accepted Claim count must be 9';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 9 THEN
    RAISE EXCEPTION 'LAMA supporting EvidenceBinding count must be 9';
  END IF;
END $$;

COMMIT;
