BEGIN;

-- Canonical scope: Oink Games `藪の中` original edition (2010), Japanese physical base game only.
-- The 2021 `藪の中 新版` changes player count, components and rules, so it is explicitly excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('publisher:oink:in-a-grove:2010-ja','https://oinkgames.com/ja/games/analog/in-a-grove/','藪の中 — オインクゲームズ 旧版公式商品ページ','publisher_product_page','オインクゲームズ','physical','ja','original-2010','{"authority":"publisher","audit_date":"2026-08-25","scope":"original_2010_identity_and_core_rules"}'::jsonb),
('publisher:oink:in-a-grove:2021-revised-ja','https://oinkgames.com/ja/games/analog/in-a-grove-new/','藪の中 新版 — オインクゲームズ公式商品ページ','publisher_product_page','オインクゲームズ','physical','ja','revised-2021','{"authority":"publisher","audit_date":"2026-08-25","scope":"edition_boundary_only"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('in-a-grove:2010:identity','publisher:oink:in-a-grove:2010-ja',NULL,'藪の中','3–4 players; about 20 minutes; age 9+; released 2010; Japanese'),
('in-a-grove:2010:suspects','publisher:oink:in-a-grove:2010-ja',NULL,'ゲームの説明','eight person-shaped chips; three randomly selected suspects; numbered 2–8'),
('in-a-grove:2010:culprit','publisher:oink:in-a-grove:2010-ja',NULL,'ゲームの説明','normally the highest-numbered suspect is the culprit'),
('in-a-grove:2010:five-reversal','publisher:oink:in-a-grove:2010-ja',NULL,'ゲームの説明','if number 5 is among the suspects, the culprit condition reverses and the lowest number is the culprit'),
('in-a-grove:2010:partial-information','publisher:oink:in-a-grove:2010-ja',NULL,'ゲームの説明','each player sees only two of the three suspect numbers before deducing the culprit'),
('in-a-grove:2010:bluff','publisher:oink:in-a-grove:2010-ja',NULL,'ゲームの説明','after deducing, a player may accuse truthfully or manipulate information to mislead following players'),
('in-a-grove:2021:edition-boundary','publisher:oink:in-a-grove:2021-revised-ja',NULL,'藪の中 新版','2021 revised edition; 2–5 players; upgraded components and updated rules; distinct from 2010 original')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='in-a-grove' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'In a Grove canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical In a Grove Work row is required'; END IF;

  UPDATE public.games SET
    title='藪の中',title_ja='藪の中',title_en='In a Grove',
    description='3人の容疑者について各プレイヤーが一部だけ異なる情報を見て、犯人を推理しながら他プレイヤーを出し抜く推理・ブラフゲーム。',
    summary='3人の容疑者のうち通常は最大の数字が犯人。ただし5が含まれる事件では最小の数字が犯人になる。各プレイヤーは容疑者2人だけを見て推理する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://oinkgames.com/ja/games/analog/in-a-grove/',
    source_url='https://oinkgames.com/ja/games/analog/in-a-grove/',official_url='https://oinkgames.com/ja/games/analog/in-a-grove/',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='藪の中 旧版（2010年）',language_code='ja',publisher='オインクゲームズ',
    source_revision='Oink Games original 2010 Japanese edition; 2021 revised edition and digital implementations excluded; audited 2026-08-25',
    min_players=3,max_players=4,play_time=20,min_age=9,published_year=2010,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='藪の中 旧版（2010年）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='oink-original-2010'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','藪の中 旧版（2010年）',
      'Oink Games original 2010 Japanese edition; 2021 revised edition and digital implementations excluded; audited 2026-08-25',
      true,'oink-original-2010','physical','オインクゲームズ','active','source_bound',
      ARRAY['publisher:oink:in-a-grove:2010-ja','publisher:oink:in-a-grove:2021-revised-ja']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Oink Games original 2010 Japanese edition; 2021 revised edition and digital implementations excluded; audited 2026-08-25',
      publisher_name='オインクゲームズ',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:oink:in-a-grove:2010-ja','publisher:oink:in-a-grove:2021-revised-ja']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'setup.suspects','setup','人型チップからランダムに3枚を容疑者として伏せて並べ、この3人の中から犯人を推理する。',10,'source_bound','in-a-grove:rule:setup.suspects','in-a-grove:binding:setup.suspects','https://oinkgames.com/ja/games/analog/in-a-grove/','in-a-grove:2010:suspects','{}'::jsonb),
  (v_ruleset_id,'culprit.highest','effect','通常は、3人の容疑者のうち数字が最も大きい人型チップが犯人になる。',20,'source_bound','in-a-grove:rule:culprit.highest','in-a-grove:binding:culprit.highest','https://oinkgames.com/ja/games/analog/in-a-grove/','in-a-grove:2010:culprit','{}'::jsonb),
  (v_ruleset_id,'culprit.five-reversal','effect','容疑者3人の中に数字5のチップが含まれている場合は犯人条件が逆転し、最も小さい数字のチップが犯人になる。',30,'source_bound','in-a-grove:rule:culprit.five-reversal','in-a-grove:binding:culprit.five-reversal','https://oinkgames.com/ja/games/analog/in-a-grove/','in-a-grove:2010:five-reversal','{}'::jsonb),
  (v_ruleset_id,'action.inspect','action','各プレイヤーは3人の容疑者のうち2人の数字だけを見て、その限られた情報から犯人を推理する。',40,'source_bound','in-a-grove:rule:action.inspect','in-a-grove:binding:action.inspect','https://oinkgames.com/ja/games/analog/in-a-grove/','in-a-grove:2010:partial-information','{}'::jsonb),
  (v_ruleset_id,'action.accuse-or-bluff','action','犯人を推理した後は、正しいと思う犯人へ賭けるだけでなく、後続プレイヤーを惑わせるように情報を操作してブラフすることもできる。',50,'source_bound','in-a-grove:rule:action.accuse-or-bluff','in-a-grove:binding:action.accuse-or-bluff','https://oinkgames.com/ja/games/analog/in-a-grove/','in-a-grove:2010:bluff','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'in-a-grove:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_product_page_normalization","audit_date":"2026-08-25","scope":"in_a_grove_original_2010"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'in-a-grove:binding:'||rn.rule_id,'in-a-grove:rule:'||rn.rule_id,'publisher:oink:in-a-grove:2010-ja',
    rn.source_locator,'supports','{"review":"publisher_product_page"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 5 THEN RAISE EXCEPTION 'In a Grove source-bound RuleNode count must be 5'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 5 THEN RAISE EXCEPTION 'In a Grove accepted Claim count must be 5'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 5 THEN RAISE EXCEPTION 'In a Grove supporting EvidenceBinding count must be 5'; END IF;
END $$;

COMMIT;
