BEGIN;

-- Canonical scope: Mattel Japan UNO product B7696 and its Japanese instruction sheet.
-- Product #42003, older 108-card revisions, UNO Flip, and other UNO variants remain separate.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:mattel-jp:uno:b7696-product','https://mattel.co.jp/toys/mattel_games/mattel_games-10936/','ウノ — Mattel Japan product B7696','publisher_product_page','マテル・インターナショナル株式会社','physical','ja','current-b7696-product','{"authority":"official_japanese_product_page","audit_date":"2026-08-27","scope":"identity_players_age_product_code"}'::jsonb),
('publisher:mattel-jp:uno:b7696-rules-2017','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','ウノ B7696 — 日本語取扱説明書 B7696-ZZ70-G2_JJ2','publisher_rulebook','マテル・インターナショナル株式会社','physical','ja','B7696-ZZ70-G2_JJ2-2017','{"authority":"official_japanese_rulebook","audit_date":"2026-08-27","scope":"b7696_112_card_rules","copyright":"2017","remark":"Wild Shuffle Hands rule updated 2017-03-01"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('unob7696:product:identity','publisher:mattel-jp:uno:b7696-product',NULL,'ウノ','品番B7696; 2～10人; 7才以上; シャッフルワイルドカードと白いワイルドカードを含む'),
('unob7696:rules:contents','publisher:mattel-jp:uno:b7696-rules-2017',1,'カードの説明と枚数','数字76枚、ドロー2/リバース/スキップ各8枚、ワイルド4枚、ワイルドドロー4 4枚、シャッフルワイルド1枚、白いワイルド3枚、合計112枚'),
('unob7696:rules:setup','publisher:mattel-jp:uno:b7696-rules-2017',1,'はじめ方','最大数字を引いた人が親; 各7枚; 残りを引き札; 1枚を捨て札にする'),
('unob7696:rules:turn','publisher:mattel-jp:uno:b7696-rules-2017',1,'早分かりルール','場札と同じ数字・色・記号、またはワイルド系を1枚出す; 出せなければ1枚引く'),
('unob7696:rules:draw-two','publisher:mattel-jp:uno:b7696-rules-2017',1,'ドロー2','次の人は2枚引き、その手番では捨てられない'),
('unob7696:rules:reverse','publisher:mattel-jp:uno:b7696-rules-2017',1,'リバース','順番の方向を逆にする'),
('unob7696:rules:skip','publisher:mattel-jp:uno:b7696-rules-2017',1,'スキップ','次の人の手番を1回飛ばす'),
('unob7696:rules:wild','publisher:mattel-jp:uno:b7696-rules-2017',1,'ワイルド','場札に関係なく出せ、好きな色を宣言する'),
('unob7696:rules:wild-draw-four','publisher:mattel-jp:uno:b7696-rules-2017',1,'ワイルド ドロー4を使うとき（チャレンジ）','次の人に4枚引かせる; 不正使用へのチャレンジと6枚ペナルティ'),
('unob7696:rules:shuffle-wild','publisher:mattel-jp:uno:b7696-rules-2017',1,'シャッフルワイルド','全員の手札を集めてシャッフルし、左隣から1枚ずつ配り直して色を指定する'),
('unob7696:rules:white-wild','publisher:mattel-jp:uno:b7696-rules-2017',1,'白いワイルドのルール','ゲーム前に合意したルールを書き、1～3枚使える'),
('unob7696:rules:uno-call','publisher:mattel-jp:uno:b7696-rules-2017',1,'あがるとき','残り1枚になるときUNOと宣言; 次の人がカードを出すまでに指摘されると2枚引く'),
('unob7696:rules:round-end','publisher:mattel-jp:uno:b7696-rules-2017',1,'上がり方','最初の1人が手札をすべて捨てるとラウンド終了'),
('unob7696:rules:scoring','publisher:mattel-jp:uno:b7696-rules-2017',1,'得点の計算','上がった人は他の人の残り手札の点数合計を得点する'),
('unob7696:rules:game-end','publisher:mattel-jp:uno:b7696-rules-2017',1,'得点の計算','国際ルールでは最初に500点へ到達した人がゲームの勝者'),
('unob7696:rules:two-player','publisher:mattel-jp:uno:b7696-rules-2017',1,'2人遊び／罰点方式','2人ではリバースとスキップを出した人が続けてプレイし、ドロー2/ドロー4後も手番が戻る')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='uno' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'UNO row absent; skipping catalog-bound seed'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical UNO Work row is required'; END IF;

  UPDATE public.games SET
    title='UNO',title_ja='ウノ',title_en='UNO',
    description='場札と同じ色・数字・記号のカードを出して手札をなくす、マテル日本版B7696のカードゲーム。',
    summary='各手番で場札と色・数字・記号が一致するカードかワイルド系を1枚出す。出せなければ1枚引き、残り1枚になるときはUNOと宣言する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://mattel.co.jp/toys/mattel_games/mattel_games-10936/',
    source_url='https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf',
    official_url='https://mattel.co.jp/toys/mattel_games/mattel_games-10936/',source_trust='official_publisher',content_review_status='human_reviewed',is_official=true,
    edition_label='ウノ B7696（日本語版・シャッフルワイルド）',language_code='ja',publisher='マテル・インターナショナル株式会社',
    source_revision='B7696-ZZ70-G2_JJ2 ©2017; Wild Shuffle Hands rule updated 2017-03-01; audited 2026-08-27',
    min_players=2,max_players=10,play_time=NULL,play_time_min_minutes=NULL,play_time_max_minutes=NULL,min_age=7,published_year=NULL,updated_at=now()
  WHERE id=v_game_id;

  UPDATE public.rule_sets
  SET is_active=false,updated_at=now()
  WHERE game_id=v_game_id AND is_active=true
    AND NOT (COALESCE(edition_label,'')='ウノ B7696（日本語版・シャッフルワイルド）'
      AND COALESCE(revision_label,'')='B7696-ZZ70-G2_JJ2-2017');

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='ウノ B7696（日本語版・シャッフルワイルド）'
    AND COALESCE(platform,'')='physical' AND COALESCE(revision_label,'')='B7696-ZZ70-G2_JJ2-2017'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,revision_label,platform,publisher_name,status,verification_status,source_ids)
    VALUES(v_game_id,v_work_id,1,'1.0','ja','ウノ B7696（日本語版・シャッフルワイルド）',
      'B7696-ZZ70-G2_JJ2 ©2017; Wild Shuffle Hands rule updated 2017-03-01; audited 2026-08-27',true,
      'B7696-ZZ70-G2_JJ2-2017','physical','マテル・インターナショナル株式会社','active','source_bound',
      ARRAY['publisher:mattel-jp:uno:b7696-product','publisher:mattel-jp:uno:b7696-rules-2017']::text[])
    RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='B7696-ZZ70-G2_JJ2 ©2017; Wild Shuffle Hands rule updated 2017-03-01; audited 2026-08-27',
      publisher_name='マテル・インターナショナル株式会社',
      source_ids=ARRAY['publisher:mattel-jp:uno:b7696-product','publisher:mattel-jp:uno:b7696-rules-2017']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'setup.base','setup','各プレイヤーが1枚引き、数字が最も大きい人を親にする。親は各プレイヤーへ7枚ずつ伏せて配り、残りを引き札の山にして一番上の1枚を表向きの捨て札にする。',10,'source_bound','unob7696:rule:setup.base','unob7696:binding:setup.base','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:setup','{}'::jsonb),
  (v_ruleset_id,'turn.match','turn','親の左隣から時計回りに始め、場のカードと同じ数字・色・記号のカード、またはワイルド系カードを1枚出す。',20,'source_bound','unob7696:rule:turn.match','unob7696:binding:turn.match','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:turn','{}'::jsonb),
  (v_ruleset_id,'turn.draw','turn','出せるカードがなければ引き札から1枚引く。引いたカードが使える場合はすぐ出せるが、使えない場合は次の人へ手番が移る。',30,'source_bound','unob7696:rule:turn.draw','unob7696:binding:turn.draw','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:turn','{}'::jsonb),
  (v_ruleset_id,'action.draw-two','effect','ドロー2を出すと次のプレイヤーは2枚引き、その手番ではカードを出せない。',40,'source_bound','unob7696:rule:action.draw-two','unob7696:binding:action.draw-two','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:draw-two','{}'::jsonb),
  (v_ruleset_id,'action.reverse','effect','リバースを出すと順番の進む方向が逆になる。',50,'source_bound','unob7696:rule:action.reverse','unob7696:binding:action.reverse','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:reverse','{}'::jsonb),
  (v_ruleset_id,'action.skip','effect','スキップを出すと次のプレイヤーの手番を1回飛ばす。',60,'source_bound','unob7696:rule:action.skip','unob7696:binding:action.skip','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:skip','{}'::jsonb),
  (v_ruleset_id,'action.wild','effect','ワイルドは場のカードに関係なく出せ、出したプレイヤーが次に続く色を指定する。',70,'source_bound','unob7696:rule:action.wild','unob7696:binding:action.wild','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:wild','{}'::jsonb),
  (v_ruleset_id,'action.wild-draw-four','condition','ワイルドドロー4を出すと次のプレイヤーは4枚引いて手番を失う。不正使用を疑う次のプレイヤーはチャレンジでき、不正なら出した側が4枚、正当ならチャレンジ側が合計6枚引く。',80,'source_bound','unob7696:rule:action.wild-draw-four','unob7696:binding:action.wild-draw-four','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:wild-draw-four','{}'::jsonb),
  (v_ruleset_id,'action.shuffle-wild','effect','シャッフルワイルドを出したら全員の手札を集めてシャッフルし、自分の左隣から1枚ずつすべて配り直す。その後、好きな色を指定する。',90,'source_bound','unob7696:rule:action.shuffle-wild','unob7696:binding:action.shuffle-wild','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:shuffle-wild','{}'::jsonb),
  (v_ruleset_id,'variant.white-wild','condition','白いワイルドにはゲーム前に相談して好きなルールを書き、使う枚数を1～3枚から決める。出したら書かれたルールに従い、好きな色を指定する。',100,'source_bound','unob7696:rule:variant.white-wild','unob7696:binding:variant.white-wild','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:white-wild','{}'::jsonb),
  (v_ruleset_id,'round.uno-call','condition','手札が2枚から1枚になるカードを出すときはUNOと宣言する。宣言を忘れ、次のプレイヤーがカードを出すまでに指摘された場合は2枚引く。',110,'source_bound','unob7696:rule:round.uno-call','unob7696:binding:round.uno-call','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:uno-call','{}'::jsonb),
  (v_ruleset_id,'round.end','round_end','最初に手札をすべて捨てたプレイヤーが出た時点でラウンドを終了する。',120,'source_bound','unob7696:rule:round.end','unob7696:binding:round.end','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:round-end','{}'::jsonb),
  (v_ruleset_id,'score.round','scoring','ラウンドで上がったプレイヤーは、他のプレイヤーに残ったカードの合計点を得点する。数字カードは額面、ドロー2・リバース・スキップは20点、ワイルドとワイルドドロー4は50点、シャッフルワイルドと白いワイルドは40点。',130,'source_bound','unob7696:rule:score.round','unob7696:binding:score.round','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:scoring','{}'::jsonb),
  (v_ruleset_id,'game.win-500','victory','国際ルールでは、ラウンド得点を累積して最初に500点へ到達したプレイヤーがゲームに勝つ。',140,'source_bound','unob7696:rule:game.win-500','unob7696:binding:game.win-500','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:game-end','{}'::jsonb),
  (v_ruleset_id,'variant.two-player','condition','2人プレイではリバースとスキップを出したプレイヤーが続けてもう一度プレイする。ドロー2またはワイルドドロー4で相手がカードを引いた後も、手番は出した側へ戻る。',150,'source_bound','unob7696:rule:variant.two-player','unob7696:binding:variant.two-player','https://mattel.co.jp/wp-content/uploads/2022/06/B7696-ZZ70-G2_JJ2_IS.pdf','unob7696:rules:two-player','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'unob7696:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"official_japanese_rulebook_normalization","audit_date":"2026-08-27","scope":"mattel_japan_uno_b7696"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'unob7696:binding:'||rn.rule_id,'unob7696:rule:'||rn.rule_id,'publisher:mattel-jp:uno:b7696-rules-2017',rn.source_locator,'supports',
    '{"review":"official_japanese_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 15 THEN
    RAISE EXCEPTION 'UNO B7696 RuleNode contract failed';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND lifecycle_status='accepted') <> 15 THEN
    RAISE EXCEPTION 'UNO B7696 Claim contract failed';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 15 THEN
    RAISE EXCEPTION 'UNO B7696 EvidenceBinding contract failed';
  END IF;
  IF (SELECT count(*) FROM public.rule_sets WHERE game_id=v_game_id AND is_active=true AND verification_status='source_bound') <> 1 THEN
    RAISE EXCEPTION 'UNO B7696 active RuleSet contract failed';
  END IF;
END $$;

COMMIT;
