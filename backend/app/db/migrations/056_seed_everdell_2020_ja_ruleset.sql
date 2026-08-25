BEGIN;

-- Canonical scope: Arclight Japanese `エバーデール 完全日本語版` (2020-01-09), base game only.
-- Pearlbrook, Spirecrest, Bellfaire, Newleaf, Mistwood, Duo, Farshore, digital implementations and solo-specific variants are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:arclight:everdell:2020-ja','https://arclightgames.jp/product/%E3%82%A8%E3%83%90%E3%83%BC%E3%83%87%E3%83%BC%E3%83%AB/','エバーデール 完全日本語版 — アークライト商品ページ','publisher_product_page','アークライト','physical','ja','japanese-release-2020-01-09','{"authority":"publisher_distributor","audit_date":"2026-08-25","scope":"japanese_base_identity_components"}'::jsonb),
('publisher:arclight:everdell:errata-ja','https://arclightgames.jp/%E3%80%90%E3%82%A8%E3%83%A9%E3%83%83%E3%82%BF%E3%80%91%E3%82%A8%E3%83%90%E3%83%BC%E3%83%87%E3%83%BC%E3%83%AB/','エバーデール 完全日本語版 — 公式エラッタ','publisher_errata','アークライト','physical','ja','first-and-second-printing-errata','{"authority":"publisher_distributor","audit_date":"2026-08-25","scope":"japanese_base_errata"}'::jsonb),
('publisher:arclight:everdell:faq-ja','https://arclightgames.jp/006everdellfaq/','エバーデール 完全日本語版 — 公式FAQ','publisher_faq','アークライト','physical','ja','faq-2022-06-29','{"authority":"publisher_distributor","audit_date":"2026-08-25","scope":"japanese_base_faq"}'::jsonb),
('publisher:starling:everdell:core-rulebook-en','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','Everdell — Core Game Rulebook','publisher_rulebook','Starling Games','physical','en','core-rulebook-current','{"authority":"publisher","audit_date":"2026-08-25","scope":"everdell_base_game_core_rules"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('everdell:rules:overview','publisher:starling:everdell:core-rulebook-en',2,'Overview','each turn choose exactly one: place a worker, play a card, or prepare for season; finished after autumn when no more actions'),
('everdell:rules:setup','publisher:starling:everdell:core-rulebook-en',5,'Setup','board/tree/resources; 3 forest cards at 2p or 4 at 3-4p; four basic and four special events; 8 meadow cards; starting workers/cards'),
('everdell:rules:play-card','publisher:starling:everdell:core-rulebook-en',9,'Play a Card','play one card from hand or Meadow by paying listed cost; critter can be free once via its construction using occupied token'),
('everdell:rules:city-hand','publisher:starling:everdell:core-rulebook-en',10,'City / Drawing Cards','city maximum 15 spaces; strict hand limit 8; Meadow card is immediately replenished'),
('everdell:rules:prepare-season','publisher:starling:everdell:core-rulebook-en',11,'Prepare for Season','when all workers are placed and player cannot or does not wish to play a card, retrieve workers and take next-season bonuses; players advance seasons independently'),
('everdell:rules:season-bonuses','publisher:starling:everdell:core-rulebook-en',12,'Prepare for Season','spring: +1 worker and production; summer: +1 worker and draw up to 2 Meadow cards; autumn: +2 workers and production'),
('everdell:rules:end-game','publisher:starling:everdell:core-rulebook-en',13,'End Game','after autumn, pass when no more actions or no desire to act; all others continue; highest total points wins; ties by most Events then leftover resources'),
('everdell:rules:open-destination-faq','publisher:arclight:everdell:faq-ja',NULL,'ルール説明書9ページ「赤の目的地カード」','owner gains 1 VP only when another player places a worker on the owner city card marked OPEN'),
('everdell:rules:season-errata','publisher:arclight:everdell:errata-ja',NULL,'第1刷 ルール説明書12ページ「③次の季節の準備」','game begins at the end of winter and progresses toward the next winter'),
('everdell:rules:judge-errata','publisher:arclight:everdell:errata-ja',NULL,'動物カード《裁判官》','Judge effect cannot be combined with other play-a-card effects')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='everdell' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Everdell canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Everdell Work row is required'; END IF;

  UPDATE public.games SET
    title='エバーデール 完全日本語版',title_ja='エバーデール 完全日本語版',title_en='Everdell',
    description='森の動物たちの街を、ワーカー配置とカードプレイで発展させる建物建築ゲーム。',
    summary='手番では労働者配置、カードプレイ、次の季節の準備のいずれか1つを行い、冬の終わりから秋まで街を発展させて得点を競う。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://arclightgames.jp/product/%E3%82%A8%E3%83%90%E3%83%BC%E3%83%87%E3%83%BC%E3%83%AB/',
    source_url='https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603',
    official_url='https://arclightgames.jp/product/%E3%82%A8%E3%83%90%E3%83%BC%E3%83%87%E3%83%BC%E3%83%AB/',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='エバーデール 完全日本語版（2020年1月9日）',language_code='ja',publisher='Starling Games',
    source_revision='Arclight Japanese base release 2020-01-09 with official Japanese errata/FAQ; Starling base core rulebook; expansions and derivative products excluded; audited 2026-08-25',
    min_players=1,max_players=4,play_time=80,min_age=10,published_year=2020,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='エバーデール 完全日本語版（2020年1月9日）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='arclight-2020-ja-starling-core'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','エバーデール 完全日本語版（2020年1月9日）',
      'Arclight Japanese base release 2020-01-09 with official Japanese errata/FAQ; Starling base core rulebook; expansions and derivative products excluded; audited 2026-08-25',
      true,'arclight-2020-ja-starling-core','physical','Starling Games','active','source_bound',
      ARRAY['publisher:arclight:everdell:2020-ja','publisher:arclight:everdell:errata-ja','publisher:arclight:everdell:faq-ja','publisher:starling:everdell:core-rulebook-en']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Arclight Japanese base release 2020-01-09 with official Japanese errata/FAQ; Starling base core rulebook; expansions and derivative products excluded; audited 2026-08-25',
      publisher_name='Starling Games',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:arclight:everdell:2020-ja','publisher:arclight:everdell:errata-ja','publisher:arclight:everdell:faq-ja','publisher:starling:everdell:core-rulebook-en']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'setup.base','setup','ボードと永遠の樹を置き、資源と得点・扉トークンを準備する。森カードは2人なら3枚、3～4人なら4枚、基本イベント4枚と特殊イベント4枚、草原には山札から8枚を表向きに並べる。各プレイヤーは労働者2体で開始し、初期手札は手番順に5・6・7・8枚となる。',10,'source_bound','everdell:rule:setup.base','everdell:binding:setup.base','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:setup','{}'::jsonb),
  (v_ruleset_id,'turn.choice','turn','各手番では「労働者を配置する」「カードを1枚プレイする」「次の季節の準備をする」のいずれか1つだけを行う。',20,'source_bound','everdell:rule:turn.choice','everdell:binding:turn.choice','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:overview','{}'::jsonb),
  (v_ruleset_id,'action.place-worker','action','労働者を配置できる場所に1体置き、その場所に示された資源または効果をただちに得る。複数配置可能と示されていない場所は、ほかの労働者がいる間は使用できない。',30,'source_bound','everdell:rule:action.place-worker','everdell:binding:action.place-worker','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:overview','{}'::jsonb),
  (v_ruleset_id,'action.play-card','action','手札または草原からカード1枚を選び、記載されたコストを支払って自分の街にプレイする。',40,'source_bound','everdell:rule:action.play-card','everdell:binding:action.play-card','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:play-card','{}'::jsonb),
  (v_ruleset_id,'action.free-critter','effect','動物カードに対応する建物が自分の街にある場合、その建物に扉トークンを置くことで、ベリーのコストを支払わずその動物を1回だけプレイできる。',50,'source_bound','everdell:rule:action.free-critter','everdell:binding:action.free-critter','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:play-card','{}'::jsonb),
  (v_ruleset_id,'city.limit','effect','自分の街は原則15スペースまでで、通常はカード1枚が1スペースを使う。イベントカードはこの15枚制限には数えない。',60,'source_bound','everdell:rule:city.limit','everdell:binding:city.limit','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:city-hand','{}'::jsonb),
  (v_ruleset_id,'hand.limit','effect','手札上限は8枚で、8枚を超えて保持することはできない。草原からカードがプレイされたら、ただちに山札から補充して8枚に戻す。',70,'source_bound','everdell:rule:hand.limit','everdell:binding:hand.limit','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:city-hand','{}'::jsonb),
  (v_ruleset_id,'season.prepare','turn','配置した労働者がすべて盤上にあり、カードをプレイできない、またはプレイしたくない場合は次の季節の準備を行う。配置済み労働者をすべて回収し、次の季節の労働者とボーナスを得る。各プレイヤーは別々のタイミングで季節を進めてよい。',80,'source_bound','everdell:rule:season.prepare','everdell:binding:season.prepare','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:prepare-season','{}'::jsonb),
  (v_ruleset_id,'season.bonuses','effect','春は労働者1体を追加して緑の生産カードを起動する。夏は労働者1体を追加し、可能なら草原から最大2枚引く。秋は労働者2体を追加して緑の生産カードを起動する。',90,'source_bound','everdell:rule:season.bonuses','everdell:binding:season.bonuses','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:season-bonuses','{}'::jsonb),
  (v_ruleset_id,'destination.open-owner-bonus','effect','〈オープン〉表示のある自分の街の目的地カードに他のプレイヤーが労働者を置いたとき、そのカードの所有者は銀行から勝利点トークン1個を得る。自分自身の労働者を置いた場合はこの所有者ボーナスを得ない。',100,'source_bound','everdell:rule:destination.open-owner-bonus','everdell:binding:destination.open-owner-bonus','https://arclightgames.jp/006everdellfaq/','everdell:rules:open-destination-faq','{}'::jsonb),
  (v_ruleset_id,'game.end-score','game_end','秋を終え、これ以上行動できない、または行動しないことを選んだプレイヤーはパスする。全員が終えたらカード得点、得点トークン、紫カードのボーナス、旅、イベントを合計し、最多得点者が勝つ。同点はイベント達成数、その後残り資源数で判定する。',110,'source_bound','everdell:rule:game.end-score','everdell:binding:game.end-score','https://cdn.shopify.com/s/files/1/0559/8245/6947/files/Everdell_Core_Game_Rulebook-web_res.pdf?v=1647463603','everdell:rules:end-game','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'everdell:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-25","scope":"everdell_2020_japanese_base"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'everdell:binding:'||rn.rule_id,'everdell:rule:'||rn.rule_id,
    CASE WHEN rn.rule_id='destination.open-owner-bonus' THEN 'publisher:arclight:everdell:faq-ja' ELSE 'publisher:starling:everdell:core-rulebook-en' END,
    rn.source_locator,'supports','{"review":"publisher_rule_or_faq"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 11 THEN RAISE EXCEPTION 'Everdell source-bound RuleNode count must be 11'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 11 THEN RAISE EXCEPTION 'Everdell accepted Claim count must be 11'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 11 THEN RAISE EXCEPTION 'Everdell supporting EvidenceBinding count must be 11'; END IF;
END $$;

COMMIT;
