BEGIN;

-- Canonical scope: Russian Railroads original 2013 physical base game.
-- Ultimate Railroads and all expansions/modules are excluded because the publisher documents rules changes.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:hig:russian-railroads:rules-en-2013','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','Russian Railroads — original English rulebook','publisher_rulebook','Hans im Glück / Z-Man Games','physical','en','2013-original','{"authority":"publisher","audit_date":"2026-08-24","scope":"original_2013_base_game"}'::jsonb),
('publisher:hig:ultimate-railroads:product','https://www.hans-im-glueck.de/en/game/ultimate-railroads-2/','Ultimate Railroads','publisher_product_page','Hans im Glück','physical','en','current-product-page','{"authority":"publisher","audit_date":"2026-08-24","scope":"edition_boundary_context"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('russian-railroads:rules:setup','publisher:hig:russian-railroads:rules-en-2013','Game setup','player boards, workers, track markers, locomotive, industry marker and starting rouble'),
('russian-railroads:rules:worker-placement','publisher:hig:russian-railroads:rules-en-2013','Course of play','players place the required workers on an available action space and resolve it immediately'),
('russian-railroads:rules:track','publisher:hig:russian-railroads:rules-en-2013','Track extension','advance track markers while preserving track order'),
('russian-railroads:rules:locomotive','publisher:hig:russian-railroads:rules-en-2013','Locomotives and factories','locomotive reach limits which route spaces score'),
('russian-railroads:rules:industry','publisher:hig:russian-railroads:rules-en-2013','Industrialization','advance the industry marker and resolve factory effects reached'),
('russian-railroads:rules:engineers','publisher:hig:russian-railroads:rules-en-2013','Engineers','hired engineers become private action spaces'),
('russian-railroads:rules:round-scoring','publisher:hig:russian-railroads:rules-en-2013','Scoring','score railroads and industrialization at the end of each round'),
('russian-railroads:rules:round-count','publisher:hig:russian-railroads:rules-en-2013','Game length','seven rounds with four players; six rounds with two or three players'),
('russian-railroads:rules:end','publisher:hig:russian-railroads:rules-en-2013','Game end','final scoring and end-game bonuses; highest victory-point total wins'),
('russian-railroads:edition:boundary','publisher:hig:ultimate-railroads:product','Description','Ultimate Railroads revises the 2013 Russian Railroads product and must not be treated as the same rules revision')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='russian-railroads' LIMIT 1;
  IF v_game_id IS NULL OR v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Russian Railroads Game/Work row is required'; END IF;

  UPDATE public.games SET
    title='Russian Railroads',title_ja='ロシアン・レイルロード',title_en='Russian Railroads',
    description='鉄道会社の経営者として、ワーカー配置で線路・機関車・工業化を発展させ、各ラウンドの得点を伸ばす重量級戦略ゲーム。',
    summary='空いているアクションへワーカーを置き、3路線の線路、機関車、工業トラックを発展させる。各ラウンド終了時に鉄道と工業化を得点し、最終的に最も多くの勝利点を得たプレイヤーが勝つ。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf',
    source_url='https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf',
    official_url='https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='Russian Railroads（2013 original）',language_code='ja',publisher='Hans im Glück / Z-Man Games',
    source_revision='Russian Railroads original 2013 English rulebook; Ultimate Railroads changes excluded; audited 2026-08-24',
    min_players=2,max_players=4,play_time=120,min_age=13,published_year=2013,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Russian Railroads（2013 original）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='hig-zman-2013-original-en'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','Russian Railroads（2013 original）',
      'Russian Railroads original 2013 English rulebook; Ultimate Railroads changes excluded; audited 2026-08-24',
      true,'hig-zman-2013-original-en','physical','Hans im Glück / Z-Man Games','active','source_bound',
      ARRAY['publisher:hig:russian-railroads:rules-en-2013','publisher:hig:ultimate-railroads:product']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',
      source_revision='Russian Railroads original 2013 English rulebook; Ultimate Railroads changes excluded; audited 2026-08-24',
      is_active=true,publisher_name='Hans im Glück / Z-Man Games',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:hig:russian-railroads:rules-en-2013','publisher:hig:ultimate-railroads:product']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.base','setup','各プレイヤーは自分のプレイヤーボードを受け取り、3路線の開始位置に黒い線路マーカーを置く。トランスシベリア鉄道に最初の機関車を置き、工業マーカーを工業トラックの開始位置へ置き、開始用のワーカーと1ルーブルを受け取る。',10,'source_bound','russian-railroads:rule:setup.base','russian-railroads:binding:setup.base','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:setup','{}'::jsonb),
  (v_ruleset_id,'round.worker-placement','turn','手番では、未占有のアクションスペースにそのスペースが要求する数のワーカーをまとめて置き、対応するアクションを直ちに実行する。全員が配置を終えるまで手番を繰り返す。',20,'source_bound','russian-railroads:rule:round.worker-placement','russian-railroads:binding:round.worker-placement','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:worker-placement','{}'::jsonb),
  (v_ruleset_id,'action.track-extension','action','線路延伸アクションでは指定された歩数だけ線路マーカーを進める。後から解禁される線路は、その前段階の線路を追い越して進めることはできない。',30,'source_bound','russian-railroads:rule:action.track-extension','russian-railroads:binding:action.track-extension','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:track','{}'::jsonb),
  (v_ruleset_id,'action.locomotive','action','機関車は各路線で得点できる到達範囲を決める。線路マーカーが機関車の到達範囲より先へ進んでいても、その先の区間はそのラウンドの鉄道得点には含まれない。',40,'source_bound','russian-railroads:rule:action.locomotive','russian-railroads:binding:action.locomotive','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:locomotive','{}'::jsonb),
  (v_ruleset_id,'action.industrialization','action','工業化アクションでは工業マーカーを工業トラック上で進める。工業マーカーが工場を通過すると、その工場の効果を解決して工業化を続ける。',50,'source_bound','russian-railroads:rule:action.industrialization','russian-railroads:binding:action.industrialization','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:industry','{}'::jsonb),
  (v_ruleset_id,'action.engineer','action','雇用したエンジニアは自分の前に置き、そのエンジニアのアクションスペースは以後その所有者だけがワーカー配置に利用できる。',60,'source_bound','russian-railroads:rule:action.engineer','russian-railroads:binding:action.engineer','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:engineers','{}'::jsonb),
  (v_ruleset_id,'round.scoring','scoring','各ラウンド終了時に3本の鉄道路線と工業化を得点する。鉄道は機関車が到達できる範囲だけを評価し、より高度な線路ほど1区間あたりの得点が高い。',70,'source_bound','russian-railroads:rule:round.scoring','russian-railroads:binding:round.scoring','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:round-scoring','{}'::jsonb),
  (v_ruleset_id,'game.round-count','condition','4人ゲームは7ラウンド、2人または3人ゲームは6ラウンドで行う。',80,'source_bound','russian-railroads:rule:game.round-count','russian-railroads:binding:game.round-count','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:round-count','{}'::jsonb),
  (v_ruleset_id,'game.end','game_end','最終ラウンドの通常得点とゲーム終了時のボーナスを処理した後、勝利点が最も多いプレイヤーが勝つ。',90,'source_bound','russian-railroads:rule:game.end','russian-railroads:binding:game.end','https://www.hans-im-glueck.de/_Resources/Persistent/3519279e01e92a55671e94ef8cf567c7e41e81f3/RRR_rules_en.pdf','russian-railroads:rules:end','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'russian-railroads:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"russian_railroads_2013_original"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'russian-railroads:binding:'||rn.rule_id,'russian-railroads:rule:'||rn.rule_id,'publisher:hig:russian-railroads:rules-en-2013',rn.source_locator,'supports',
    '{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 9 THEN
    RAISE EXCEPTION 'Russian Railroads source-bound RuleNode count must be 9';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 9 THEN
    RAISE EXCEPTION 'Russian Railroads accepted Claim count must be 9';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 9 THEN
    RAISE EXCEPTION 'Russian Railroads supporting EvidenceBinding count must be 9';
  END IF;
END $$;

COMMIT;
