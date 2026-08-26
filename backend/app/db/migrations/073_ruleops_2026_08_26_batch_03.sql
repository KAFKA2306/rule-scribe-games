BEGIN;

-- RuleOps game: ito / アークライト ito 基本版（2019年8月8日） / arclight-ito-base-2019-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('ito:arclight-rules-page','https://arclightgames.jp/product/ito/','ito — publisher_rules_page','publisher_rules_page',NULL,'physical','ja','current official base-product rules page accessed 2026-08-26','{"authority":"publisher_rules_page","ruleops":true,"scope":"ito 基本版（アークライト、2019）— クモノイト / アカイイト"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('ito:locator:kumonoito-setup','ito:arclight-rules-page','クモノイト > ゲームの概要 > ゲームの準備','クモノイト > ゲームの概要 > ゲームの準備'),
('ito:locator:kumonoito-theme','ito:arclight-rules-page','クモノイト > テーマ決定 / ナンバーの表現','クモノイト > テーマ決定 / ナンバーの表現'),
('ito:locator:kumonoito-no-turn-order','ito:arclight-rules-page','クモノイト > ナンバーの表現 / カードを出す','クモノイト > ナンバーの表現 / カードを出す'),
('ito:locator:kumonoito-failure-life','ito:arclight-rules-page','クモノイト > カードを出す / 失敗時の処理','クモノイト > カードを出す / 失敗時の処理'),
('ito:locator:kumonoito-stage-clear','ito:arclight-rules-page','クモノイト > ステージクリア','クモノイト > ステージクリア'),
('ito:locator:kumonoito-stage-progression','ito:arclight-rules-page','クモノイト > 次のステージの準備','クモノイト > 次のステージの準備'),
('ito:locator:kumonoito-third-stage','ito:arclight-rules-page','クモノイト > 第3ステージ / モモちゃん','クモノイト > 第3ステージ / モモちゃん'),
('ito:locator:kumonoito-victory','ito:arclight-rules-page','クモノイト > ゲーム終了','クモノイト > ゲーム終了'),
('ito:locator:akaito-mode','ito:arclight-rules-page','アカイイト > クモノイトルールとの違い / 運命の相手','アカイイト > クモノイトルールとの違い / 運命の相手')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='ito' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game ito absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for ito'; END IF;

  UPDATE public.games SET
    title='ito',
    identity_status='verified', identity_source='https://arclightgames.jp/product/ito/',
    source_url='https://arclightgames.jp/product/ito/', source_trust='official_publisher',
    content_review_status='review_required', is_official=true,
    edition_label='アークライト ito 基本版（2019年8月8日）', language_code='ja',
    source_revision='arclight-ito-base-2019-accessed-2026-08-26', updated_at=now(), rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='アークライト ito 基本版（2019年8月8日）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='arclight-ito-base-2019-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','アークライト ito 基本版（2019年8月8日）',
      'arclight-ito-base-2019-accessed-2026-08-26',true,'arclight-ito-base-2019-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['ito:arclight-rules-page']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='arclight-ito-base-2019-accessed-2026-08-26',source_ids=ARRAY['ito:arclight-rules-page']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'kumonoito-setup','setup','クモノイトではナンバーカードを混ぜて各プレイヤーに1枚ずつ配り、テーマカードを山札にし、共有ライフを3に設定してクモノシートを場にする。',10,'source_bound','ito:rule:kumonoito-setup','ito:binding:kumonoito-setup','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-setup','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'kumonoito-theme','action','クモノイトではテーマカードから候補を出して今回のテーマを決め、そのテーマに沿って自分のナンバーを数字そのものを言わずに表現する。',20,'source_bound','ito:rule:kumonoito-theme','ito:binding:kumonoito-theme','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-theme','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'kumonoito-no-turn-order','turn','クモノイトのナンバー表現には手番順がなく、全員の表現後は相談しながらカードを小さい順になるよう1枚ずつ場へ出す。',30,'source_bound','ito:rule:kumonoito-no-turn-order','ito:binding:kumonoito-no-turn-order','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-no-turn-order','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'kumonoito-failure-life','effect','クモノイトで順番を誤った場合、その時点で正しく出せなくなったカードを脇へ置き、その枚数ぶん共有ライフを失う。',40,'source_bound','ito:rule:kumonoito-failure-life','ito:binding:kumonoito-failure-life','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-failure-life','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'kumonoito-stage-clear','condition','クモノイトでは全員の手札を出し切り、ライフが残っていればそのステージをクリアする。',50,'source_bound','ito:rule:kumonoito-stage-clear','ito:binding:kumonoito-stage-clear','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-stage-clear','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'kumonoito-stage-progression','setup','次のステージでは共有ライフを最大3まで1回復し（2人プレイでは回復しない）、ナンバーカードを混ぜ直して第2ステージは2枚、第3ステージは3枚ずつ配る。',60,'source_bound','ito:rule:kumonoito-stage-progression','ito:binding:kumonoito-stage-progression','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-stage-progression','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'kumonoito-third-stage','effect','クモノイトの第3ステージでは追加のナンバーカード1枚を表向きにする『モモちゃん』を加える。',70,'source_bound','ito:rule:kumonoito-third-stage','ito:binding:kumonoito-third-stage','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-third-stage','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'kumonoito-victory','victory','クモノイトは第3ステージをクリアすれば全員の勝利で、途中で共有ライフが0になれば全員の敗北となる。',80,'source_bound','ito:rule:kumonoito-victory','ito:binding:kumonoito-victory','https://arclightgames.jp/product/ito/','ito:locator:kumonoito-victory','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'akaito-mode','action','アカイイトでは手札は常に1枚で、スタートプレイヤーがテーマを決め、時計回りにナンバーを表現し、2人のナンバー合計が100になる相手を探す。',90,'source_bound','ito:rule:akaito-mode','ito:binding:akaito-mode','https://arclightgames.jp/product/ito/','ito:locator:akaito-mode','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'ito:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-batch-03"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('ito:binding:kumonoito-setup','ito:rule:kumonoito-setup','ito:arclight-rules-page','ito:locator:kumonoito-setup','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:kumonoito-theme','ito:rule:kumonoito-theme','ito:arclight-rules-page','ito:locator:kumonoito-theme','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:kumonoito-no-turn-order','ito:rule:kumonoito-no-turn-order','ito:arclight-rules-page','ito:locator:kumonoito-no-turn-order','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:kumonoito-failure-life','ito:rule:kumonoito-failure-life','ito:arclight-rules-page','ito:locator:kumonoito-failure-life','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:kumonoito-stage-clear','ito:rule:kumonoito-stage-clear','ito:arclight-rules-page','ito:locator:kumonoito-stage-clear','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:kumonoito-stage-progression','ito:rule:kumonoito-stage-progression','ito:arclight-rules-page','ito:locator:kumonoito-stage-progression','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:kumonoito-third-stage','ito:rule:kumonoito-third-stage','ito:arclight-rules-page','ito:locator:kumonoito-third-stage','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:kumonoito-victory','ito:rule:kumonoito-victory','ito:arclight-rules-page','ito:locator:kumonoito-victory','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('ito:binding:akaito-mode','ito:rule:akaito-mode','ito:arclight-rules-page','ito:locator:akaito-mode','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 9
    THEN RAISE EXCEPTION 'RuleOps ito RuleNode count must be 9'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 9
    THEN RAISE EXCEPTION 'RuleOps ito Claim count must be 9'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 9
    THEN RAISE EXCEPTION 'RuleOps ito EvidenceBinding count must be 9'; END IF;
END $$;

-- RuleOps game: scythe / サイズ – 大鎌戦役 – 完全日本語版（2017年12月9日） / arclight-scythe-ja-2017-errata-current-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('scythe:arclight-product','https://arclightgames.jp/product/%E3%82%B5%E3%82%A4%E3%82%BA-%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/','サイズ - 大鎌戦役 - — publisher_product_page','publisher_product_page',NULL,'physical','ja','Japanese base product page accessed 2026-08-26','{"authority":"publisher_product_page","ruleops":true,"scope":"サイズ – 大鎌戦役 – 完全日本語版（Arclight / Stonemaier Games）"}'::jsonb),
('scythe:arclight-errata','https://arclightgames.jp/%E3%80%90%E3%82%A8%E3%83%A9%E3%83%83%E3%82%BF%E3%80%91%E3%82%B5%E3%82%A4%E3%82%BA%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/','サイズ - 大鎌戦役 - — publisher_errata','publisher_errata',NULL,'physical','ja','current Japanese errata accessed 2026-08-26','{"authority":"publisher_errata","ruleops":true,"scope":"サイズ – 大鎌戦役 – 完全日本語版（Arclight / Stonemaier Games）"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('scythe:locator:action-row-correction','scythe:arclight-errata','ルール説明書p.10『6.プレイ手順』訂正','ルール説明書p.10『6.プレイ手順』訂正'),
('scythe:locator:worker-only-controlled-area','scythe:arclight-errata','ルール説明書p.11 移動アクション訂正','ルール説明書p.11 移動アクション訂正'),
('scythe:locator:trade-popularity','scythe:arclight-errata','ルール説明書p.12 交易アクション訂正','ルール説明書p.12 交易アクション訂正')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='scythe' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game scythe absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for scythe'; END IF;

  UPDATE public.games SET
    title='サイズ - 大鎌戦役 -',
    identity_status='verified', identity_source='https://arclightgames.jp/product/%E3%82%B5%E3%82%A4%E3%82%BA-%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/',
    source_url='https://arclightgames.jp/product/%E3%82%B5%E3%82%A4%E3%82%BA-%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/', source_trust='official_publisher',
    content_review_status='review_required', is_official=true,
    edition_label='サイズ – 大鎌戦役 – 完全日本語版（2017年12月9日）', language_code='ja',
    source_revision='arclight-scythe-ja-2017-errata-current-accessed-2026-08-26', updated_at=now(), rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='サイズ – 大鎌戦役 – 完全日本語版（2017年12月9日）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='arclight-scythe-ja-2017-errata-current-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','サイズ – 大鎌戦役 – 完全日本語版（2017年12月9日）',
      'arclight-scythe-ja-2017-errata-current-accessed-2026-08-26',true,'arclight-scythe-ja-2017-errata-current-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['scythe:arclight-product','scythe:arclight-errata']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='arclight-scythe-ja-2017-errata-current-accessed-2026-08-26',source_ids=ARRAY['scythe:arclight-product','scythe:arclight-errata']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'action-row-correction','action','プレイヤーマットの上段アクションは増強・生産・移動・交易、下段アクションは改良・展開・建設・徴兵である。',10,'source_bound','scythe:rule:action-row-correction','scythe:binding:action-row-correction','https://arclightgames.jp/%E3%80%90%E3%82%A8%E3%83%A9%E3%83%83%E3%82%BF%E3%80%91%E3%82%B5%E3%82%A4%E3%82%BA%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/','scythe:locator:action-row-correction','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'worker-only-controlled-area','effect','対戦相手の労働者だけが支配する区域へ戦闘ユニットが移動した場合、その区域で移動を止め、相手の労働者は退却し、その区域にあった資源は残る。',20,'source_bound','scythe:rule:worker-only-controlled-area','scythe:binding:worker-only-controlled-area','https://arclightgames.jp/%E3%80%90%E3%82%A8%E3%83%A9%E3%83%83%E3%82%BF%E3%80%91%E3%82%B5%E3%82%A4%E3%82%BA%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/','scythe:locator:worker-only-controlled-area','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'trade-popularity','effect','交易アクションで選べる支持の上昇量は1である。',30,'source_bound','scythe:rule:trade-popularity','scythe:binding:trade-popularity','https://arclightgames.jp/%E3%80%90%E3%82%A8%E3%83%A9%E3%83%83%E3%82%BF%E3%80%91%E3%82%B5%E3%82%A4%E3%82%BA%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/','scythe:locator:trade-popularity','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'scythe:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-batch-03"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('scythe:binding:action-row-correction','scythe:rule:action-row-correction','scythe:arclight-errata','scythe:locator:action-row-correction','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('scythe:binding:worker-only-controlled-area','scythe:rule:worker-only-controlled-area','scythe:arclight-errata','scythe:locator:worker-only-controlled-area','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now()),
('scythe:binding:trade-popularity','scythe:rule:trade-popularity','scythe:arclight-errata','scythe:locator:trade-popularity','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-03"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 3
    THEN RAISE EXCEPTION 'RuleOps scythe RuleNode count must be 3'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 3
    THEN RAISE EXCEPTION 'RuleOps scythe Claim count must be 3'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 3
    THEN RAISE EXCEPTION 'RuleOps scythe EvidenceBinding count must be 3'; END IF;
END $$;

COMMIT;
