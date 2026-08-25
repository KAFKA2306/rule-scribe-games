BEGIN;

-- Canonical scope: Hobby Japan Japanese `パンデミック：新たなる試練` (2013-07), Z-MAN base Pandemic.
-- Previous Japanese edition, expansions, Legacy, Hot Zone, Rapid Response, The Cure, solo/survival/scenario rules are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:hobbyjapan:pandemic:new-ja','https://hobbyjapan.games/pandemic_new/','パンデミック：新たなる試練 — ホビージャパン日本語版商品ページ','publisher_product_page','ホビージャパン','physical','ja','japanese-release-2013-07','{"authority":"publisher_distributor","audit_date":"2026-08-25","scope":"japanese_new_version_identity_and_errata"}'::jsonb),
('publisher:zman:pandemic:rulebook-en','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','Pandemic — Z-MAN Games Rulebook','publisher_rulebook','Z-MAN Games','physical','en','current-official-rulebook','{"authority":"publisher","audit_date":"2026-08-25","scope":"pandemic_base_game"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('pandemic:rules:setup-board','publisher:zman:pandemic:rulebook-en',2,'Setup','place board, six research stations and disease cubes; one research station in Atlanta; outbreak marker at 0; cure markers vial-side up'),
('pandemic:rules:setup-infection','publisher:zman:pandemic:rulebook-en',3,'Setup','infection rate starts at left-most 2; infect nine cities with 3/2/1 cubes'),
('pandemic:rules:setup-player-deck','publisher:zman:pandemic:rulebook-en',3,'Prepare the Player Deck','4/5/6 epidemic cards set introductory/standard/heroic difficulty; one epidemic shuffled into each pile'),
('pandemic:rules:turn','publisher:zman:pandemic:rulebook-en',3,'Play','turn: do four actions, draw two player cards and resolve epidemics/hand limit, then infect cities'),
('pandemic:rules:movement','publisher:zman:pandemic:rulebook-en',4,'Actions','drive/ferry, direct flight, charter flight and shuttle flight movement actions'),
('pandemic:rules:build','publisher:zman:pandemic:rulebook-en',4,'Build a Research Station','discard matching city card to build research station in current city'),
('pandemic:rules:treat','publisher:zman:pandemic:rulebook-en',4,'Treat Disease','remove one cube in current city; if disease is cured remove all cubes of that color there'),
('pandemic:rules:share','publisher:zman:pandemic:rulebook-en',4,'Share Knowledge','players in same city give/take the city card matching that city'),
('pandemic:rules:cure','publisher:zman:pandemic:rulebook-en',4,'Discover a Cure','at research station discard five same-color city cards to cure that disease'),
('pandemic:rules:epidemic','publisher:zman:pandemic:rulebook-en',6,'Epidemics','increase infection rate; infect bottom-deck city with three cubes; intensify by shuffling infection discard onto infection deck'),
('pandemic:rules:outbreak','publisher:zman:pandemic:rulebook-en',7,'Outbreaks','outbreak advances track and places one cube in connected cities; chain reactions may occur; eighth outbreak loses'),
('pandemic:rules:game-end','publisher:zman:pandemic:rulebook-en',7,'Game End','win immediately when all four diseases are cured; lose on eighth outbreak, insufficient disease cubes, or inability to draw two player cards')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='pandemic' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Pandemic canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Pandemic Work row is required'; END IF;

  UPDATE public.games SET
    title='パンデミック：新たなる試練',title_ja='パンデミック：新たなる試練',title_en='Pandemic',
    description='4種類の病原体の治療薬発見を目指し、役割ごとの能力を生かして感染拡大を抑える協力ゲーム。',
    summary='各手番で4アクションを行い、プレイヤーカードを2枚引いた後に都市へ感染を広げる。4種類すべての治療薬を発見すれば全員が勝利する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://hobbyjapan.games/pandemic_new/',
    source_url='https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf',
    official_url='https://hobbyjapan.games/pandemic_new/',source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='パンデミック：新たなる試練 日本語版（2013年7月）',language_code='ja',publisher='Z-MAN Games',
    source_revision='Hobby Japan Japanese new version released 2013-07; Z-MAN official base rulebook; previous edition and Pandemic-family variants excluded; audited 2026-08-25',
    min_players=2,max_players=4,play_time=45,min_age=8,published_year=2013,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='パンデミック：新たなる試練 日本語版（2013年7月）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='zman-base-rulebook-current'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','パンデミック：新たなる試練 日本語版（2013年7月）',
      'Hobby Japan Japanese new version released 2013-07; Z-MAN official base rulebook; previous edition and Pandemic-family variants excluded; audited 2026-08-25',
      true,'zman-base-rulebook-current','physical','Z-MAN Games','active','source_bound',
      ARRAY['publisher:hobbyjapan:pandemic:new-ja','publisher:zman:pandemic:rulebook-en']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Hobby Japan Japanese new version released 2013-07; Z-MAN official base rulebook; previous edition and Pandemic-family variants excluded; audited 2026-08-25',
      publisher_name='Z-MAN Games',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:hobbyjapan:pandemic:new-ja','publisher:zman:pandemic:rulebook-en']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'setup.board','setup','ボードを中央に置き、病原体コマを4色に分ける。調査基地1個をアトランタに置き、アウトブレイクマーカーを0、4個の治療薬マーカーを未発見側で準備する。',10,'source_bound','pandemic:rule:setup.board','pandemic:binding:setup.board','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:setup-board','{}'::jsonb),
  (v_ruleset_id,'setup.infection','setup','感染率マーカーを最初の2に置く。感染カードを3枚ずつ3回公開し、最初の3都市に各3個、次の3都市に各2個、最後の3都市に各1個の対応色病原体コマを置く。',20,'source_bound','pandemic:rule:setup.infection','pandemic:binding:setup.infection','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:setup-infection','{}'::jsonb),
  (v_ruleset_id,'setup.difficulty','setup','難易度に応じてエピデミックカードを4枚（初級）、5枚（標準）、6枚（上級）使い、プレイヤーデッキを同数の山に分けて各山へ1枚ずつ混ぜてから積み重ねる。',30,'source_bound','pandemic:rule:setup.difficulty','pandemic:binding:setup.difficulty','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:setup-player-deck','{}'::jsonb),
  (v_ruleset_id,'turn.phases','turn','手番は「4アクションを行う」「プレイヤーカードを2枚引く」「都市を感染させる」の順で進む。',40,'source_bound','pandemic:rule:turn.phases','pandemic:binding:turn.phases','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:turn','{}'::jsonb),
  (v_ruleset_id,'action.movement','action','移動には、白線でつながる都市への移動、目的地カードを捨てる直行便、現在地カードを捨てるチャーター便、調査基地間を移動するシャトル便がある。各移動は1アクションを使う。',50,'source_bound','pandemic:rule:action.movement','pandemic:binding:action.movement','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:movement','{}'::jsonb),
  (v_ruleset_id,'action.build-station','action','現在地と同じ都市カードを捨てると、その都市に調査基地を1個建設できる。',60,'source_bound','pandemic:rule:action.build-station','pandemic:binding:action.build-station','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:build','{}'::jsonb),
  (v_ruleset_id,'action.treat','action','現在地の病原体コマを1個取り除く。対応する病原体の治療薬を発見済みなら、その色の病原体コマを現在地からすべて取り除く。',70,'source_bound','pandemic:rule:action.treat','pandemic:binding:action.treat','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:treat','{}'::jsonb),
  (v_ruleset_id,'action.share','action','同じ都市にいる2人の間で、その現在地と同じ都市カードを渡すか受け取ることができる。',80,'source_bound','pandemic:rule:action.share','pandemic:binding:action.share','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:share','{}'::jsonb),
  (v_ruleset_id,'action.discover-cure','action','調査基地にいるプレイヤーが同じ病原体色の都市カード5枚を捨てると、その病原体の治療薬を発見する。',90,'source_bound','pandemic:rule:action.discover-cure','pandemic:binding:action.discover-cure','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:cure','{}'::jsonb),
  (v_ruleset_id,'epidemic.resolve','effect','エピデミックでは感染率を1段階上げ、感染デッキの一番下の都市に病原体コマ3個を置き、その後感染捨て札だけを混ぜて感染デッキの上に戻す。',100,'source_bound','pandemic:rule:epidemic.resolve','pandemic:binding:epidemic.resolve','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:epidemic','{}'::jsonb),
  (v_ruleset_id,'outbreak.resolve','effect','都市に同色の病原体コマがすでに3個ある状態でさらに置く必要があるとアウトブレイクが発生し、アウトブレイクトラックを1進め、接続する各都市へその色を1個ずつ置く。連鎖アウトブレイクも起こり得る。',110,'source_bound','pandemic:rule:outbreak.resolve','pandemic:binding:outbreak.resolve','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:outbreak','{}'::jsonb),
  (v_ruleset_id,'game.end','game_end','4種類すべての治療薬を発見した時点で全員が勝利する。アウトブレイクが8回に達する、必要な病原体コマを置けない、またはアクション後にプレイヤーカードを2枚引けない場合は全員が敗北する。',120,'source_bound','pandemic:rule:game.end','pandemic:binding:game.end','https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/Pandemic_Rulebook.pdf','pandemic:rules:game-end','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'pandemic:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-25","scope":"pandemic_2013_japanese_new_version"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'pandemic:binding:'||rn.rule_id,'pandemic:rule:'||rn.rule_id,'publisher:zman:pandemic:rulebook-en',rn.source_locator,'supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 12 THEN RAISE EXCEPTION 'Pandemic source-bound RuleNode count must be 12'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 12 THEN RAISE EXCEPTION 'Pandemic accepted Claim count must be 12'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 12 THEN RAISE EXCEPTION 'Pandemic supporting EvidenceBinding count must be 12'; END IF;
END $$;

COMMIT;