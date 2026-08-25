BEGIN;

-- Canonical scope: Arclight Japanese Century: Spice Road base game released 2017-06-24.
-- Eastern Wonders, A New World, Golem editions, combined-game rules, promos, and other Century products remain separate.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'publisher:arclight:century-spice-road:2017-product',
  'https://arclightgames.jp/product/%E3%82%BB%E3%83%B3%E3%83%81%E3%83%A5%E3%83%AA%E3%83%BC%E3%82%B9%E3%83%91%E3%82%A4%E3%82%B9%E3%83%AD%E3%83%BC%E3%83%89/',
  'センチュリー：スパイスロード 完全日本語版 — Arclight product page',
  'publisher_product_page','Arclight','physical','ja','2017-06-24 Japanese edition',
  '{"authority":"official_japanese_product_page","audit_date":"2026-08-26","scope":"japanese_product_identity_components_player_count_play_time_age"}'::jsonb
),
(
  'publisher:arclight:century-spice-road:2017-errata',
  'https://arclightgames.jp/%E3%80%90%E3%82%A8%E3%83%A9%E3%83%83%E3%82%BF%E3%80%91%E3%82%BB%E3%83%B3%E3%83%81%E3%83%A5%E3%83%AA%E3%83%BC%E3%82%B9%E3%83%91%E3%82%A4%E3%82%B9%E3%83%AD%E3%83%BC%E3%83%89/',
  'センチュリー：スパイスロード 完全日本語版 — Arclight errata',
  'publisher_errata','Arclight','physical','ja','Japanese edition errata',
  '{"authority":"official_japanese_errata","audit_date":"2026-08-26","scope":"starting_spices_and_print_corrections"}'::jsonb
),
(
  'publisher:nextmove:century-spice-road:2024-rulebook',
  'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf',
  'Century: Spice Road — Next Move / Plan B Games official rules ©2024',
  'publisher_rulebook','Plan B Games Inc.','physical','en','2024 base rulebook',
  '{"authority":"official_publisher_rulebook","audit_date":"2026-08-26","scope":"base_setup_turn_actions_limits_end_scoring"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('century-spice-road:2017:identity','publisher:arclight:century-spice-road:2017-product','商品概要','2017-06-24; Plan B Games; 2–5 players; 30–45 min; age 8+'),
('century-spice-road:2017:starting-spices','publisher:arclight:century-spice-road:2017-errata','ルール説明書 ■1.ゲームの準備','4th and 5th players: 3 yellow + 1 red'),
('century-spice-road:2024:setup','publisher:nextmove:century-spice-road:2024-rulebook','Game Setup','5 Point cards; 6 Merchant cards; starting cards; caravan; starting cubes'),
('century-spice-road:2024:turn-actions','publisher:nextmove:century-spice-road:2024-rulebook','Taking a Turn','Choose exactly one: Play, Acquire, Rest, Claim'),
('century-spice-road:2024:play','publisher:nextmove:century-spice-road:2024-rulebook','Play','Spice, Upgrade, and Trade card effects'),
('century-spice-road:2024:acquire','publisher:nextmove:century-spice-road:2024-rulebook','Acquire','Pay one cube on each Merchant card to the left; leftmost is free'),
('century-spice-road:2024:rest','publisher:nextmove:century-spice-road:2024-rulebook','Rest','Return all previously played face-up cards to hand'),
('century-spice-road:2024:claim','publisher:nextmove:century-spice-road:2024-rulebook','Claim','Pay required cubes; take Point card; left positions can award coins'),
('century-spice-road:2024:caravan-limit','publisher:nextmove:century-spice-road:2024-rulebook','Caravan Limit','Maximum 10 cubes at end of turn'),
('century-spice-road:2024:end','publisher:nextmove:century-spice-road:2024-rulebook','Game End','5th Point card, or 6th in 2–3 player game; finish current round'),
('century-spice-road:2024:scoring','publisher:nextmove:century-spice-road:2024-rulebook','Game End','Point cards + coins + non-yellow cubes; most points wins; last player wins tie')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='century-spice-road' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'Century: Spice Road row absent; skipping catalog-bound seed'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required'; END IF;

  UPDATE public.games SET
    title='センチュリー：スパイスロード',title_ja='センチュリー：スパイスロード',title_en='Century: Spice Road',
    description='香辛料商人として商人カードを使い、スパイスを生産・交換・強化しながら勝利点カードを獲得するカードゲーム。',
    summary='手番ではカードをプレイする、商人カードを獲得する、休息する、勝利点カードを獲得する、の4アクションから1つを選ぶ。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://arclightgames.jp/product/%E3%82%BB%E3%83%B3%E3%83%81%E3%83%A5%E3%83%AA%E3%83%BC%E3%82%B9%E3%83%91%E3%82%A4%E3%82%B9%E3%83%AD%E3%83%BC%E3%83%89/',
    source_url='https://arclightgames.jp/product/%E3%82%BB%E3%83%B3%E3%83%81%E3%83%A5%E3%83%AA%E3%83%BC%E3%82%B9%E3%83%91%E3%82%A4%E3%82%B9%E3%83%AD%E3%83%BC%E3%83%89/',
    official_url='https://arclightgames.jp/product/%E3%82%BB%E3%83%B3%E3%83%81%E3%83%A5%E3%83%AA%E3%83%BC%E3%82%B9%E3%83%91%E3%82%A4%E3%82%B9%E3%83%AD%E3%83%BC%E3%83%89/',
    source_trust='official_publisher',content_review_status='human_reviewed',is_official=true,
    edition_label='センチュリー：スパイスロード 完全日本語版（2017年6月24日）',language_code='ja',publisher='Plan B Games Inc.',
    source_revision='Arclight Japanese product/errata + Plan B/Next Move 2024 base rulebook; audited 2026-08-26',
    min_players=2,max_players=5,play_time=45,min_age=8,published_year=2017,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='センチュリー：スパイスロード 完全日本語版（2017年6月24日）'
    AND COALESCE(platform,'')='physical' AND COALESCE(revision_label,'')='arclight-2017-ja-nextmove-2024-base'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,revision_label,platform,publisher_name,status,verification_status,source_ids)
    VALUES(v_game_id,v_work_id,1,'1.0','ja','センチュリー：スパイスロード 完全日本語版（2017年6月24日）',
      'Arclight Japanese product/errata + Plan B/Next Move 2024 base rulebook; audited 2026-08-26',true,
      'arclight-2017-ja-nextmove-2024-base','physical','Plan B Games Inc.','active','source_bound',
      ARRAY['publisher:arclight:century-spice-road:2017-product','publisher:arclight:century-spice-road:2017-errata','publisher:nextmove:century-spice-road:2024-rulebook']::text[])
    RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='Arclight Japanese product/errata + Plan B/Next Move 2024 base rulebook; audited 2026-08-26',
      source_ids=ARRAY['publisher:arclight:century-spice-road:2017-product','publisher:arclight:century-spice-road:2017-errata','publisher:nextmove:century-spice-road:2024-rulebook']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'setup.market','setup','勝利点カードを5枚、商人カードを6枚表向きに並べ、人数の2倍の金貨を左端の勝利点カード上、同数の銀貨を左から2番目の上に置く。',10,'source_bound','century-spice-road:rule:setup.market','century-spice-road:binding:setup.market','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:setup','{}'::jsonb),
  (v_ruleset_id,'setup.players','setup','各プレイヤーは「Create 2」と「Upgrade 2」の初期商人カード、キャラバンカード、手番順に応じた初期スパイスを受け取る。4・5番手は黄色3個と赤1個を受け取る。',20,'source_bound','century-spice-road:rule:setup.players','century-spice-road:binding:setup.players','https://arclightgames.jp/%E3%80%90%E3%82%A8%E3%83%A9%E3%83%83%E3%82%BF%E3%80%91%E3%82%BB%E3%83%B3%E3%83%81%E3%83%A5%E3%83%AA%E3%83%BC%E3%82%B9%E3%83%91%E3%82%A4%E3%82%B9%E3%83%AD%E3%83%BC%E3%83%89/','century-spice-road:2017:starting-spices','{}'::jsonb),
  (v_ruleset_id,'turn.choose_action','turn','自分の手番では「カードをプレイ」「商人カードを獲得」「休息」「勝利点カードを獲得」の4つから1つだけを行う。',30,'source_bound','century-spice-road:rule:turn.choose_action','century-spice-road:binding:turn.choose_action','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:turn-actions','{}'::jsonb),
  (v_ruleset_id,'action.play','action','商人カードをプレイすると、スパイス獲得、スパイスの段階アップ、またはカードに示された交換を行う。交換カードは必要なスパイスがある限り同じ手番中に複数回適用できる。',40,'source_bound','century-spice-road:rule:action.play','century-spice-road:binding:action.play','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:play','{}'::jsonb),
  (v_ruleset_id,'action.acquire','action','商人カードを獲得するには、選ぶカードより左側の各商人カード上へキャラバンから任意のスパイス1個ずつを置く。左端のカードは無料で獲得できる。',50,'source_bound','century-spice-road:rule:action.acquire','century-spice-road:binding:action.acquire','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:acquire','{}'::jsonb),
  (v_ruleset_id,'action.rest','action','休息を選ぶと、自分の前に表向きでプレイ済みの商人カードをすべて手札へ戻す。',60,'source_bound','century-spice-road:rule:action.rest','century-spice-road:binding:action.rest','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:rest','{}'::jsonb),
  (v_ruleset_id,'action.claim','action','勝利点カードに示されたスパイスをすべて支払うとそのカードを獲得する。左端または左から2番目のカードなら、残っている金貨または銀貨も受け取る。',70,'source_bound','century-spice-road:rule:action.claim','century-spice-road:binding:action.claim','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:claim','{}'::jsonb),
  (v_ruleset_id,'limit.caravan','condition','手番終了時、キャラバンに保持できるスパイスは最大10個。超えている場合は任意のスパイスを戻して10個にする。',80,'source_bound','century-spice-road:rule:limit.caravan','century-spice-road:binding:limit.caravan','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:caravan-limit','{}'::jsonb),
  (v_ruleset_id,'end.trigger','round_end','誰かが5枚目の勝利点カードを獲得したらゲーム終了を発生させる。2～3人ゲームでは6枚目で発生し、そのラウンドを最後まで行う。',90,'source_bound','century-spice-road:rule:end.trigger','century-spice-road:binding:end.trigger','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:end','{}'::jsonb),
  (v_ruleset_id,'victory.scoring','victory','勝利点カード、金貨（各3点）、銀貨（各1点）、黄色以外の残りスパイス（各1点）を合計し、最多得点のプレイヤーが勝つ。同点なら最終ラウンドで後に手番を行ったプレイヤーが勝つ。',100,'source_bound','century-spice-road:rule:victory.scoring','century-spice-road:binding:victory.scoring','https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Century-Spice-Road-Rules_2024_compressed.pdf','century-spice-road:2024:scoring','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'century-spice-road:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"official_source_normalization","audit_date":"2026-08-26","scope":"arclight_2017_ja_base"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'century-spice-road:binding:'||rn.rule_id,'century-spice-road:rule:'||rn.rule_id,
    CASE WHEN rn.rule_id='setup.players' THEN 'publisher:arclight:century-spice-road:2017-errata' ELSE 'publisher:nextmove:century-spice-road:2024-rulebook' END,
    rn.source_locator,'supports','{"review":"official_publisher_source"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 10 THEN RAISE EXCEPTION 'Century Spice Road RuleNode count must be 10'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 10 THEN RAISE EXCEPTION 'Century Spice Road Claim count must be 10'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 10 THEN RAISE EXCEPTION 'Century Spice Road EvidenceBinding count must be 10'; END IF;
END $$;

COMMIT;