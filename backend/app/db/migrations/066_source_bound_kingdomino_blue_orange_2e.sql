BEGIN;

INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'publisher:blue-orange:kingdomino:item-03600',
  'https://www.blueorangegames.com/games/king-domino',
  'Kingdomino — Blue Orange Games product page (Item #03600)',
  'publisher_product','Blue Orange Games','physical','en','item-03600-current',
  '{"authority":"publisher_product","audit_date":"2026-08-25","scope":"identity_players_time_age_base_product"}'::jsonb
),
(
  'publisher:blue-orange:kingdomino:2e-rulebook',
  'https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf',
  'Kingdomino Rules — US 2nd Edition',
  'publisher_rulebook','Blue Orange Games','physical','en','US-2nd-Edition',
  '{"authority":"publisher_rulebook","audit_date":"2026-08-25","scope":"base_game_setup_turn_order_placement_selection_end_scoring_player_count_adjustments"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('kingdomino:product:identity','publisher:blue-orange:kingdomino:item-03600',NULL,'Kingdomino','Item #03600; ages 8+; 2-4 players; 15 minutes'),
('kingdomino:rules:objective','publisher:blue-orange:kingdomino:2e-rulebook',1,'Object of the Game','Build a 5x5 kingdom and earn the highest score from connected territories and crowns'),
('kingdomino:rules:setup','publisher:blue-orange:kingdomino:2e-rulebook',2,'Set-up','Starting tile, castle, king meeple; shuffled domino draw pile'),
('kingdomino:rules:starting-round','publisher:blue-orange:kingdomino:2e-rulebook',2,'The Starting Round','Four dominoes ordered numerically; first selection order determined randomly'),
('kingdomino:rules:turn','publisher:blue-orange:kingdomino:2e-rulebook',2,'Playing a Round','Place previously selected domino, then select a new domino; king position determines order'),
('kingdomino:rules:connection','publisher:blue-orange:kingdomino:2e-rulebook',2,'Kingdom building','5x5 maximum; connect matching terrain or starting tile; placed dominoes cannot move'),
('kingdomino:rules:discard','publisher:blue-orange:kingdomino:2e-rulebook',3,'Kingdom building','Unplaceable dominoes must be discarded; placeable dominoes cannot be discarded'),
('kingdomino:rules:selection','publisher:blue-orange:kingdomino:2e-rulebook',3,'Domino Selection','Choose an available domino in the next line and place the king on it'),
('kingdomino:rules:end','publisher:blue-orange:kingdomino:2e-rulebook',3,'End of Game','Game ends when draw pile is empty; players place their final selected domino'),
('kingdomino:rules:scoring','publisher:blue-orange:kingdomino:2e-rulebook',3,'End of Game','Each territory scores connected squares multiplied by crowns; crownless territories score zero'),
('kingdomino:rules:tiebreak','publisher:blue-orange:kingdomino:2e-rulebook',3,'End of Game','Highest score wins; tie breaks by largest territory, then shared victory'),
('kingdomino:rules:player-adjustments','publisher:blue-orange:kingdomino:2e-rulebook',4,'Adjustments','2-player uses 24 dominoes and two kings each; 3-player discards one leftover domino each round')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='kingdomino' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'Kingdomino row absent; skipping catalog-bound seed'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Kingdomino Work row is required'; END IF;

  UPDATE public.games SET
    title='キングドミノ',title_ja='キングドミノ',title_en='Kingdomino',
    description='地形ドミノを選び、同じ地形をつないで5×5の王国を作るタイル配置ゲーム。王冠を含む領地を広げて得点を競う。',
    summary='前のラウンドで選んだドミノが次の手番順を左右する。配置条件と王冠を見ながら、5×5の王国で最高得点を目指す。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://www.blueorangegames.com/games/king-domino',
    source_url='https://www.blueorangegames.com/games/king-domino',official_url='https://www.blueorangegames.com/games/king-domino',
    source_trust='official_publisher',content_review_status='human_reviewed',is_official=true,
    edition_label='Blue Orange Games US 2nd Edition / Item #03600',language_code='ja',publisher='Blue Orange Games',published_year=NULL,
    source_revision='Blue Orange Games Item #03600 + official US 2nd Edition rulebook; audited 2026-08-25',
    min_players=2,max_players=4,play_time=15,min_age=8,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Blue Orange Games US 2nd Edition / Item #03600'
    AND COALESCE(platform,'')='physical' AND COALESCE(revision_label,'')='blue-orange-us-2e'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,revision_label,platform,publisher_name,status,verification_status,source_ids)
    VALUES(v_game_id,v_work_id,1,'1.0','ja','Blue Orange Games US 2nd Edition / Item #03600',
      'Blue Orange Games Item #03600 + official US 2nd Edition rulebook; audited 2026-08-25',true,
      'blue-orange-us-2e','physical','Blue Orange Games','active','source_bound',
      ARRAY['publisher:blue-orange:kingdomino:item-03600','publisher:blue-orange:kingdomino:2e-rulebook']::text[])
    RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='Blue Orange Games Item #03600 + official US 2nd Edition rulebook; audited 2026-08-25',
      source_ids=ARRAY['publisher:blue-orange:kingdomino:item-03600','publisher:blue-orange:kingdomino:2e-rulebook']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'objective.highest_score','victory','5×5の王国を作り、つながった領地と王冠から得る合計点が最も高いプレイヤーを目指す。',10,'source_bound','kingdomino:rule:objective.highest_score','kingdomino:binding:objective.highest_score','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:objective','{}'::jsonb),
  (v_ruleset_id,'setup.base','setup','各プレイヤーはスタートタイル、城、対応する王コマを受け取り、ドミノを混ぜて山札にする。',20,'source_bound','kingdomino:rule:setup.base','kingdomino:binding:setup.base','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:setup','{}'::jsonb),
  (v_ruleset_id,'setup.starting_round','setup','最初の4枚のドミノを番号順に並べて表向きにし、最初の選択順は王コマの無作為抽選で決める。',30,'source_bound','kingdomino:rule:setup.starting_round','kingdomino:binding:setup.starting_round','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:starting-round','{}'::jsonb),
  (v_ruleset_id,'turn.place_then_select','turn','各手番では、前に選んだドミノを王国へ配置してから、次の列のドミノを1枚選ぶ。現在の王コマの位置が手番順になる。',40,'source_bound','kingdomino:rule:turn.place_then_select','kingdomino:binding:turn.place_then_select','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:turn','{}'::jsonb),
  (v_ruleset_id,'placement.connection','condition','王国は5×5を超えず、新しいドミノは同じ地形同士を辺で接続するか、どの地形とも接続できるスタートタイルにつなぐ。配置後は動かせない。',50,'source_bound','kingdomino:rule:placement.connection','kingdomino:binding:placement.connection','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:connection','{}'::jsonb),
  (v_ruleset_id,'placement.discard','condition','5×5制限または接続条件のため配置できないドミノは捨てる。合法に配置できるドミノを任意に捨てることはできない。',60,'source_bound','kingdomino:rule:placement.discard','kingdomino:binding:placement.discard','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:discard','{}'::jsonb),
  (v_ruleset_id,'selection.next_domino','action','配置後、次の列に残っているドミノから1枚を選び、自分の王コマを置いて確保する。',70,'source_bound','kingdomino:rule:selection.next_domino','kingdomino:binding:selection.next_domino','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:selection','{}'::jsonb),
  (v_ruleset_id,'end.draw_pile_empty','round_end','山札のドミノがなくなったら、最後に選んだドミノを配置してゲームを終了する。',80,'source_bound','kingdomino:rule:end.draw_pile_empty','kingdomino:binding:end.draw_pile_empty','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:end','{}'::jsonb),
  (v_ruleset_id,'scoring.territory_crowns','scoring','各領地は「縦横につながる同一地形のマス数 × その領地の王冠数」で得点する。王冠がない領地は0点。',90,'source_bound','kingdomino:rule:scoring.territory_crowns','kingdomino:binding:scoring.territory_crowns','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:scoring','{}'::jsonb),
  (v_ruleset_id,'victory.tiebreak','victory','合計点が最も高いプレイヤーが勝つ。同点なら最大の領地を持つ方が勝ち、それも同じなら勝利を分け合う。',100,'source_bound','kingdomino:rule:victory.tiebreak','kingdomino:binding:victory.tiebreak','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:tiebreak','{}'::jsonb),
  (v_ruleset_id,'setup.player_count_adjustments','setup','2人では各自王コマ2個・ランダム24枚のドミノを使う。3人では全48枚を使い、各ラウンドで誰も選ばなかった1枚を捨てる。',110,'source_bound','kingdomino:rule:setup.player_count_adjustments','kingdomino:binding:setup.player_count_adjustments','https://blueorangegames.com/webroot/img/games/rules/cfa0f38157341a002eab1100aab478ea-Kingdomino-Rules-US-2nd-Edition.pdf','kingdomino:rules:player-adjustments','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'kingdomino:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-25","scope":"kingdomino_blue_orange_us_2e"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'kingdomino:binding:'||rn.rule_id,'kingdomino:rule:'||rn.rule_id,'publisher:blue-orange:kingdomino:2e-rulebook',rn.source_locator,'supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 11 THEN RAISE EXCEPTION 'Kingdomino RuleNode count must be 11'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 11 THEN RAISE EXCEPTION 'Kingdomino Claim count must be 11'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 11 THEN RAISE EXCEPTION 'Kingdomino EvidenceBinding count must be 11'; END IF;
END $$;

COMMIT;