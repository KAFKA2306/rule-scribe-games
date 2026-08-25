BEGIN;

-- Canonical scope: Oink Games SCOUT (2021 international edition), physical base game.
-- Only mechanics stated on the current official product page are normalized here;
-- unsupported legacy setup/scoring/end details are removed rather than inferred.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES (
  'publisher:oink:scout:2021-product-ja',
  'https://oinkgames.com/ja/games/analog/scout/',
  'SCOUT — オインクゲームズ公式商品ページ',
  'publisher_product_page','オインクゲームズ','physical','ja','product-page-2021',
  '{"authority":"publisher","audit_date":"2026-08-25","scope":"identity_and_core_mechanics_only"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('scout:2021:identity','publisher:oink:scout:2021-product-ja',NULL,'SCOUT','2–5 players; about 20 minutes; age 9+; produced 2021'),
('scout:2021:hand-order','publisher:oink:scout:2021-product-ja',NULL,'ゲームの説明','cards in hand cannot be rearranged'),
('scout:2021:show','publisher:oink:scout:2021-product-ja',NULL,'ゲームの説明','on your turn you may Show a stronger same-number or consecutive-number combination'),
('scout:2021:scout','publisher:oink:scout:2021-product-ja',NULL,'ゲームの説明','on your turn you may Scout a card from the field and add it to your hand; each card has two numbers and its role/orientation is chosen when joining your hand'),
('scout:2021:edition','publisher:oink:scout:2021-product-ja',NULL,'ゲームの説明','international SCOUT changes theme/artwork from SCOUT!, supports 2–5 players and adds scoring chips')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='scout' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'SCOUT canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical SCOUT Work row is required'; END IF;

  UPDATE public.games SET
    title='SCOUT',title_ja='SCOUT',title_en='SCOUT',
    description='手札の並び順を変えず、同じ数字または連続する数字の組み合わせでショーを行うか、場からカードをスカウトして手札を強化するカードゲーム。',
    summary='手札は並べ替え不可。手番では強い組み合わせを出す「ショー」か、場のカードを手札へ加える「スカウト」を選び、カード上下の数字を活用して組み合わせを育てる。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://oinkgames.com/ja/games/analog/scout/',
    source_url='https://oinkgames.com/ja/games/analog/scout/',official_url='https://oinkgames.com/ja/games/analog/scout/',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='SCOUT（Oink Games 2021国際版）',language_code='ja',publisher='オインクゲームズ',
    source_revision='Oink Games official product page; core mechanics only; detailed setup/scoring/end remain unverified; audited 2026-08-25',
    min_players=2,max_players=5,play_time=20,min_age=9,published_year=2021,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='SCOUT（Oink Games 2021国際版）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='oink-product-page-2021'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','SCOUT（Oink Games 2021国際版）',
      'Oink Games official product page; core mechanics only; detailed setup/scoring/end remain unverified; audited 2026-08-25',
      true,'oink-product-page-2021','physical','オインクゲームズ','active','source_bound',
      ARRAY['publisher:oink:scout:2021-product-ja']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Oink Games official product page; core mechanics only; detailed setup/scoring/end remain unverified; audited 2026-08-25',
      publisher_name='オインクゲームズ',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:oink:scout:2021-product-ja']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'constraint.hand-order','condition','ゲーム中、手札のカードの並び順を変えることはできない。',10,'source_bound','scout:rule:constraint.hand-order','scout:binding:constraint.hand-order','https://oinkgames.com/ja/games/analog/scout/','scout:2021:hand-order','{}'::jsonb),
  (v_ruleset_id,'action.show','action','手番では、同じ数字または連続する数字を手札内で組み合わせ、ライバルより強い組み合わせとして「ショー」を行える。',20,'source_bound','scout:rule:action.show','scout:binding:action.show','https://oinkgames.com/ja/games/analog/scout/','scout:2021:show','{}'::jsonb),
  (v_ruleset_id,'action.scout','action','手番では、場に出ている札からカードを「スカウト」して手札に加えることもできる。カードには2つの数字があり、どちらの役割で手札に加えるかを選ぶ。',30,'source_bound','scout:rule:action.scout','scout:binding:action.scout','https://oinkgames.com/ja/games/analog/scout/','scout:2021:scout','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'scout:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_product_page_normalization","audit_date":"2026-08-25","scope":"scout_2021_core"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'scout:binding:'||rn.rule_id,'scout:rule:'||rn.rule_id,'publisher:oink:scout:2021-product-ja',
    rn.source_locator,'supports','{"review":"publisher_product_page"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 3 THEN RAISE EXCEPTION 'SCOUT source-bound RuleNode count must be 3'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 3 THEN RAISE EXCEPTION 'SCOUT accepted Claim count must be 3'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 3 THEN RAISE EXCEPTION 'SCOUT supporting EvidenceBinding count must be 3'; END IF;
END $$;

COMMIT;