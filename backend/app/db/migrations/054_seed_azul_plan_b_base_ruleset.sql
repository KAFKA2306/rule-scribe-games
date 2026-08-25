BEGIN;

-- Canonical scope: Hobby Japan Japanese base Azul (2018-02), using Plan B Games' base-game rulebook.
-- Azul Mini, Crystal Mosaic, Master Chocolatier, Duel, Stained Glass of Sintra, Summer Pavilion,
-- other derivatives/expansions, digital implementations, and tournament rules are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:hobbyjapan:azul:product-ja','https://hobbyjapan.games/azul/','アズール — ホビージャパン日本語版商品ページ','publisher_product_page','ホビージャパン','physical','ja','current-product-page','{"authority":"publisher_distributor","audit_date":"2026-08-25","scope":"japanese_base_product_identity"}'::jsonb),
('publisher:planb:azul:rules-en-2017','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','Azul — Plan B Games Rulebook','publisher_rulebook','Plan B Games Inc.','physical','en','copyright-2017','{"authority":"publisher","audit_date":"2026-08-25","scope":"azul_base_game"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('azul:rules:setup','publisher:planb:azul:rules-en-2017',1,'Game Setup','boards and scoring markers; 5/7/9 factories for 2/3/4 players; 100 tiles; four tiles per factory'),
('azul:rules:round-phases','publisher:planb:azul:rules-en-2017',1,'Gameplay','each round has Factory offer, Wall-tiling, and Preparing the next round phases'),
('azul:rules:factory-offer','publisher:planb:azul:rules-en-2017',1,'A. Factory offer','take all tiles of one color from one factory or center; remaining factory tiles move to center'),
('azul:rules:pattern-lines','publisher:planb:azul:rules-en-2017',1,'Pattern lines','place chosen tiles right-to-left in one pattern line; a line holds one color; excess goes to floor'),
('azul:rules:wall-color-limit','publisher:planb:azul:rules-en-2017',1,'A. Factory offer','cannot place a color in a pattern line when the matching wall row already contains that color'),
('azul:rules:floor-line','publisher:planb:azul:rules-en-2017',1,'Floor line','unplaceable or unwanted tiles go to floor line and score penalties during Wall-tiling'),
('azul:rules:wall-tiling','publisher:planb:azul:rules-en-2017',1,'B. Wall-tiling','for each complete pattern line move one tile to matching wall space; discard remaining tiles from that completed line'),
('azul:rules:scoring','publisher:planb:azul:rules-en-2017',2,'Scoring','new wall tile scores one if isolated; otherwise score horizontally and vertically linked groups'),
('azul:rules:floor-penalty','publisher:planb:azul:rules-en-2017',2,'Scoring','floor line loses printed points; score cannot fall below zero; starting marker also counts for penalty'),
('azul:rules:next-round','publisher:planb:azul:rules-en-2017',2,'C. Preparing the next round','starting player refills each factory with four tiles; refill bag from box lid when necessary'),
('azul:rules:game-end','publisher:planb:azul:rules-en-2017',2,'End of the game','end after Wall-tiling phase in which at least one player completes a horizontal line of five consecutive tiles'),
('azul:rules:final-scoring','publisher:planb:azul:rules-en-2017',2,'End of the game','2 points per complete horizontal line, 7 per complete vertical line, 10 per complete color set'),
('azul:rules:winner','publisher:planb:azul:rules-en-2017',2,'End of the game','most points wins; tied player with more complete horizontal lines wins; otherwise victory is shared')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='azul' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Azul canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Azul Work row is required'; END IF;

  UPDATE public.games SET
    title='アズール',title_ja='アズール',title_en='Azul',
    description='同じ色のタイルをまとめて取り、図案ラインを完成させて宮殿の壁へ配置するタイルドラフトゲーム。',
    summary='工房または中央から同色タイルを取り、図案ラインへ配置する。完成した列から壁へ1枚ずつ移して得点し、横一列5枚を完成したラウンドでゲーム終了。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://hobbyjapan.games/azul/',
    source_url='https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf',
    official_url='https://hobbyjapan.games/azul/',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='アズール 日本語版（2018年2月）',language_code='ja',publisher='Plan B Games Inc.',
    source_revision='Hobby Japan Japanese base Azul released 2018-02; Plan B Games base rulebook ©2017; derivatives/expansions excluded; audited 2026-08-25',
    min_players=2,max_players=4,play_time=45,min_age=8,published_year=2018,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='アズール 日本語版（2018年2月）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='plan-b-base-rulebook-2017'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','アズール 日本語版（2018年2月）',
      'Hobby Japan Japanese base Azul released 2018-02; Plan B Games base rulebook ©2017; derivatives/expansions excluded; audited 2026-08-25',
      true,'plan-b-base-rulebook-2017','physical','Plan B Games Inc.','active','source_bound',
      ARRAY['publisher:hobbyjapan:azul:product-ja','publisher:planb:azul:rules-en-2017']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',
      source_revision='Hobby Japan Japanese base Azul released 2018-02; Plan B Games base rulebook ©2017; derivatives/expansions excluded; audited 2026-08-25',
      is_active=true,publisher_name='Plan B Games Inc.',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:hobbyjapan:azul:product-ja','publisher:planb:azul:rules-en-2017']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.base','setup','各プレイヤーはプレイヤーボードと得点マーカーを受け取り、得点を0に置く。工房展示ボードは2人なら5枚、3人なら7枚、4人なら9枚を使う。袋には5色各20枚、計100枚のタイルを入れ、各工房に4枚ずつ置く。',10,'source_bound','azul:rule:setup.base','azul:binding:setup.base','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:setup','{}'::jsonb),
  (v_ruleset_id,'round.phases','turn','各ラウンドは「工房の提示」「壁への配置」「次ラウンドの準備」の3フェイズで進む。',20,'source_bound','azul:rule:round.phases','azul:binding:round.phases','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:round-phases','{}'::jsonb),
  (v_ruleset_id,'draft.take-color','action','手番では、任意の工房1枚から同じ色のタイルをすべて取るか、中央から同じ色のタイルをすべて取る。工房から取った場合、その工房に残ったタイルはすべて中央へ移す。',30,'source_bound','azul:rule:draft.take-color','azul:binding:draft.take-color','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:factory-offer','{}'::jsonb),
  (v_ruleset_id,'pattern.place','action','取ったタイルは1つの図案ラインへ右から左に置く。すでにタイルがある図案ラインには同じ色だけを追加でき、収まらない余剰タイルは床ラインへ置く。',40,'source_bound','azul:rule:pattern.place','azul:binding:pattern.place','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:pattern-lines','{}'::jsonb),
  (v_ruleset_id,'pattern.wall-color-limit','condition','対応する壁の横列にすでに同色タイルがある場合、その色を対応する図案ラインへ置くことはできない。',50,'source_bound','azul:rule:pattern.wall-color-limit','azul:binding:pattern.wall-color-limit','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:wall-color-limit','{}'::jsonb),
  (v_ruleset_id,'floor.line','effect','ルール上置けない、または図案ラインへ置きたくないタイルは床ラインへ左から順に置き、壁への配置フェイズで失点する。',60,'source_bound','azul:rule:floor.line','azul:binding:floor.line','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:floor-line','{}'::jsonb),
  (v_ruleset_id,'wall.tile','action','壁への配置では完成した図案ラインごとに右端のタイル1枚を対応する壁の同色マスへ移し、直ちに得点する。完成ラインの残りのタイルは箱のふたへ戻し、未完成ラインは次ラウンドへ残す。',70,'source_bound','azul:rule:wall.tile','azul:binding:wall.tile','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:wall-tiling','{}'::jsonb),
  (v_ruleset_id,'wall.scoring','scoring','壁へ置いたタイルに縦横の隣接タイルがなければ1点。隣接がある場合は、新しいタイルを含む横方向の連続タイル数と縦方向の連続タイル数をそれぞれ数えて得点する。',80,'source_bound','azul:rule:wall.scoring','azul:binding:wall.scoring','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:scoring','{}'::jsonb),
  (v_ruleset_id,'floor.penalty','effect','壁への配置フェイズ終了時、床ラインの各位置に示された点数を失う。得点は0未満にはならない。スタートプレイヤーマーカーも床ラインの失点対象になる。',90,'source_bound','azul:rule:floor.penalty','azul:binding:floor.penalty','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:floor-penalty','{}'::jsonb),
  (v_ruleset_id,'round.prepare','setup','横一列5枚を完成したプレイヤーがいなければ次ラウンドを準備する。スタートプレイヤーが各工房へ袋から4枚ずつ補充し、袋が空なら箱のふたのタイルを袋へ戻して補充を続ける。',100,'source_bound','azul:rule:round.prepare','azul:binding:round.prepare','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:next-round','{}'::jsonb),
  (v_ruleset_id,'game.end','game_end','壁への配置フェイズ終了時に、少なくとも1人が壁の横一列に連続5枚のタイルを完成していればゲームを終了する。',110,'source_bound','azul:rule:game.end','azul:binding:game.end','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:game-end','{}'::jsonb),
  (v_ruleset_id,'game.final-bonus','scoring','ゲーム終了後、完成した横一列ごとに2点、完成した縦一列ごとに7点、同色5枚を壁にすべて配置した色ごとに10点を追加する。',120,'source_bound','azul:rule:game.final-bonus','azul:binding:game.final-bonus','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:final-scoring','{}'::jsonb),
  (v_ruleset_id,'game.winner','game_end','最終得点が最も高いプレイヤーが勝つ。同点なら完成した横一列が多いプレイヤーが勝ち、それでも同点なら勝利を分け合う。',130,'source_bound','azul:rule:game.winner','azul:binding:game.winner','https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/2022/04/en-azul-rules.pdf','azul:rules:winner','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'azul:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-25","scope":"azul_base_game"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'azul:binding:'||rn.rule_id,'azul:rule:'||rn.rule_id,'publisher:planb:azul:rules-en-2017',rn.source_locator,'supports',
    '{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 13 THEN
    RAISE EXCEPTION 'Azul source-bound RuleNode count must be 13';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 13 THEN
    RAISE EXCEPTION 'Azul accepted Claim count must be 13';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 13 THEN
    RAISE EXCEPTION 'Azul supporting EvidenceBinding count must be 13';
  END IF;
END $$;

COMMIT;
