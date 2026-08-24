BEGIN;

-- Canonical scope: Hobby Japan Japanese Dominion: Second Edition (2017),
-- using Rio Grande Games' official Dominion 2nd Edition rulebook as rules authority.
-- First Edition and expansion-specific rules are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:hobbyjapan:dominion-2e-ja','https://hobbyjapan.games/dominion_2nd/','ドミニオン：第二版 — Hobby Japan Japanese edition','publisher_product_page','Hobby Japan','physical','ja','japanese-second-edition-2017','{"authority":"publisher_distributor","audit_date":"2026-08-24","scope":"japanese_edition_identity"}'::jsonb),
('publisher:rio-grande:dominion-2e-rules-2021','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','Dominion 2nd Edition — official rulebook','publisher_rulebook','Rio Grande Games','physical','en','2021-rulebook-printing','{"authority":"publisher","audit_date":"2026-08-24","scope":"dominion_second_edition_base_game"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('dominion:rules:setup-deck','publisher:rio-grande:dominion-2e-rules-2021',3,'Preparation','each player starts with 7 Coppers and 3 Estates, shuffles them, and draws 5 cards'),
('dominion:rules:setup-supply','publisher:rio-grande:dominion-2e-rules-2021',3,'Preparation','Supply uses 7 Base piles plus 10 Kingdom piles; Victory and Curse pile sizes depend on player count'),
('dominion:rules:turn-overview','publisher:rio-grande:dominion-2e-rules-2021',4,'Overview','each turn proceeds Action, Buy, then Clean-up'),
('dominion:rules:action','publisher:rio-grande:dominion-2e-rules-2021',4,'Action Phase','play one Action by default and resolve its instructions completely; +Action increases available actions'),
('dominion:rules:buy','publisher:rio-grande:dominion-2e-rules-2021',5,'Buy Phase','play any number of Treasures, then buy one card by default; gained cards go to discard pile'),
('dominion:rules:cleanup','publisher:rio-grande:dominion-2e-rules-2021',5,'Clean-up Phase','discard cards in play and remaining hand, then draw a new hand of 5'),
('dominion:rules:reshuffle','publisher:rio-grande:dominion-2e-rules-2021',8,'Additional Rules','when more cards are needed than remain in deck, shuffle discard pile under deck before continuing'),
('dominion:rules:end','publisher:rio-grande:dominion-2e-rules-2021',6,'Game End','game ends at end of turn when Province pile or any three or more Supply piles are empty'),
('dominion:rules:scoring','publisher:rio-grande:dominion-2e-rules-2021',6,'Game End','count victory points across all owned cards; highest total wins'),
('dominion:rules:tiebreak','publisher:rio-grande:dominion-2e-rules-2021',6,'Game End','among tied players fewer turns wins; equal turns share victory')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='dominion' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Dominion canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Dominion Work row is required'; END IF;

  UPDATE public.games SET
    title='Dominion',title_ja='ドミニオン：第二版',title_en='Dominion',
    description='自分のデッキを領土として育てるデッキ構築型カードゲーム。銅貨7枚と屋敷3枚の初期デッキから始め、毎手番にカードを使い、サプライから新しいカードを獲得してデッキを強化する。',
    summary='手番はアクション、購入、クリーンアップの順。属州の山札、またはサプライの3山以上が空になるとゲームが終了し、所有するカードの勝利点合計を競う。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://hobbyjapan.games/dominion_2nd/',
    source_url='https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf',
    official_url='https://hobbyjapan.games/dominion_2nd/',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='ドミニオン：第二版（ホビージャパン日本語版）',language_code='ja',publisher='Rio Grande Games / Hobby Japan',
    source_revision='Hobby Japan Japanese Second Edition (2017); Rio Grande Games Dominion 2nd Edition official rulebook, 2021 printing; audited 2026-08-24',
    min_players=2,max_players=4,play_time=30,min_age=14,published_year=2017,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='ドミニオン：第二版（ホビージャパン日本語版）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='dominion-2e-rules-2021'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','ドミニオン：第二版（ホビージャパン日本語版）',
      'Hobby Japan Japanese Second Edition (2017); Rio Grande Games Dominion 2nd Edition official rulebook, 2021 printing; audited 2026-08-24',
      true,'dominion-2e-rules-2021','physical','Rio Grande Games / Hobby Japan','active','source_bound',
      ARRAY['publisher:hobbyjapan:dominion-2e-ja','publisher:rio-grande:dominion-2e-rules-2021']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',
      source_revision='Hobby Japan Japanese Second Edition (2017); Rio Grande Games Dominion 2nd Edition official rulebook, 2021 printing; audited 2026-08-24',
      is_active=true,publisher_name='Rio Grande Games / Hobby Japan',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:hobbyjapan:dominion-2e-ja','publisher:rio-grande:dominion-2e-rules-2021']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.starting-deck','setup','各プレイヤーは銅貨7枚と屋敷3枚を受け取り、10枚をシャッフルして自分の山札にする。開始時に山札から5枚を引いて手札にする。',10,'source_bound','dominion:rule:setup.starting-deck','dominion:binding:setup.starting-deck','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:setup-deck','{}'::jsonb),
  (v_ruleset_id,'setup.supply','setup','場には銅貨・銀貨・金貨・屋敷・公領・属州・呪いの7つの基本カードの山と、選んだ10種類の王国カードの山を置き、これらをサプライとする。勝利点カードと呪いの枚数はプレイヤー人数に応じて調整する。',20,'source_bound','dominion:rule:setup.supply','dominion:binding:setup.supply','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:setup-supply','{}'::jsonb),
  (v_ruleset_id,'turn.phases','turn','各手番は「アクション」「購入」「クリーンアップ」の3フェイズをこの順に行う。',30,'source_bound','dominion:rule:turn.phases','dominion:binding:turn.phases','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:turn-overview','{}'::jsonb),
  (v_ruleset_id,'phase.action','action','アクションフェイズでは通常、手札からアクションカードを1枚プレイできる。カードの指示を順に解決し、+アクションを得た場合はその分だけ追加のアクションカードをプレイできる。',40,'source_bound','dominion:rule:phase.action','dominion:binding:phase.action','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:action','{}'::jsonb),
  (v_ruleset_id,'phase.buy','action','購入フェイズでは手札から任意枚数の財宝カードをプレイし、通常は利用可能なコインの範囲でサプライからカードを1枚購入する。購入したカードは自分の捨て札置き場に置く。+購入があれば追加で購入できる。',50,'source_bound','dominion:rule:phase.buy','dominion:binding:phase.buy','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:buy','{}'::jsonb),
  (v_ruleset_id,'phase.cleanup','turn','クリーンアップフェイズでは、場に出したカードと手札に残ったカードを捨て札置き場に置き、新しい手札として5枚を引く。手番が終わると未使用のアクション・購入・コインは失われる。',60,'source_bound','dominion:rule:phase.cleanup','dominion:binding:phase.cleanup','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:cleanup','{}'::jsonb),
  (v_ruleset_id,'deck.reshuffle','rule','山札から必要な枚数を用意できないときは、まず捨て札をシャッフルして山札の下に置き、その後で必要な処理を続ける。山札が空でも、カードが必要になるまでは捨て札をシャッフルしない。',70,'source_bound','dominion:rule:deck.reshuffle','dominion:binding:deck.reshuffle','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:reshuffle','{}'::jsonb),
  (v_ruleset_id,'game.end','game_end','手番終了時に属州の山が空、またはサプライの山が3つ以上空ならゲームを終了する。',80,'source_bound','dominion:rule:game.end','dominion:binding:game.end','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:end','{}'::jsonb),
  (v_ruleset_id,'game.scoring','scoring','ゲーム終了時、手札・山札・捨て札・場・脇に置いたカードを含む、自分が所有するすべてのカードの勝利点を合計する。最も勝利点が多いプレイヤーが勝つ。',90,'source_bound','dominion:rule:game.scoring','dominion:binding:game.scoring','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:scoring','{}'::jsonb),
  (v_ruleset_id,'game.tiebreak','scoring','勝利点が同点の場合、その同点者のうち手番回数が少ないプレイヤーが勝つ。手番回数も同じなら同点者全員が勝利する。',100,'source_bound','dominion:rule:game.tiebreak','dominion:binding:game.tiebreak','https://www.riograndegames.com/wp-content/uploads/2016/09/Dominion2nd.pdf','dominion:rules:tiebreak','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'dominion:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"dominion_second_edition_base_game"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'dominion:binding:'||rn.rule_id,'dominion:rule:'||rn.rule_id,'publisher:rio-grande:dominion-2e-rules-2021',rn.source_locator,'supports',
    '{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 10 THEN
    RAISE EXCEPTION 'Dominion source-bound RuleNode count must be 10';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 10 THEN
    RAISE EXCEPTION 'Dominion accepted Claim count must be 10';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 10 THEN
    RAISE EXCEPTION 'Dominion supporting EvidenceBinding count must be 10';
  END IF;
END $$;

COMMIT;
