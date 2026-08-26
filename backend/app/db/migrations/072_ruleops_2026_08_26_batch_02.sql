BEGIN;

-- RuleOps game: fort / Leder Games Fort core game rulebook 2020-10-15 / leder-fort-rulebook-2020-10-15-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('fort:leder-product','https://ledergames.com/products/fort','Fort — publisher_product_page','publisher_product_page',NULL,'physical','ja','current product page accessed 2026-08-26','{"authority":"publisher_product_page","ruleops":true,"scope":"Fort core game (Leder Games)"}'::jsonb),
('fort:leder-rulebook-2020-10-15','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','Fort — publisher_rulebook','publisher_rulebook',NULL,'physical','ja','2020-10-15','{"authority":"publisher_rulebook","ruleops":true,"scope":"Fort core game (Leder Games)"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('fort:locator:setup-deck','fort:leder-rulebook-2020-10-15','p.2 Basic Setup','p.2 Basic Setup'),
('fort:locator:five-phases','fort:leder-rulebook-2020-10-15','p.6 How to Play','p.6 How to Play'),
('fort:locator:play-action','fort:leder-rulebook-2020-10-15','p.6 Play a Card','p.6 Play a Card'),
('fort:locator:follow','fort:leder-rulebook-2020-10-15','p.7 Following','p.7 Following'),
('fort:locator:recruit','fort:leder-rulebook-2020-10-15','p.8 Recruit','p.8 Recruit'),
('fort:locator:end-trigger','fort:leder-rulebook-2020-10-15','p.10 End of Game','p.10 End of Game'),
('fort:locator:final-score','fort:leder-rulebook-2020-10-15','p.10 End of Game','p.10 End of Game')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='fort' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game fort absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for fort'; END IF;

  UPDATE public.games SET
    title='Fort',
    identity_status='verified', identity_source='https://ledergames.com/products/fort',
    source_url='https://ledergames.com/products/fort', source_trust='official_publisher',
    content_review_status='review_required', is_official=true,
    edition_label='Leder Games Fort core game rulebook 2020-10-15', language_code='ja',
    source_revision='leder-fort-rulebook-2020-10-15-accessed-2026-08-26', updated_at=now(), rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Leder Games Fort core game rulebook 2020-10-15'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='leder-fort-rulebook-2020-10-15-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','Leder Games Fort core game rulebook 2020-10-15',
      'leder-fort-rulebook-2020-10-15-accessed-2026-08-26',true,'leder-fort-rulebook-2020-10-15-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['fort:leder-product','fort:leder-rulebook-2020-10-15']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='leder-fort-rulebook-2020-10-15-accessed-2026-08-26',source_ids=ARRAY['fort:leder-product','fort:leder-rulebook-2020-10-15']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'setup-deck','setup','各プレイヤーは2枚のBest Friendと8枚の通常カードから10枚のデッキを作り、5枚を手札として引く。',10,'source_bound','fort:rule:setup-deck','fort:binding:setup-deck','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','fort:locator:setup-deck','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'five-phases','turn','手番はCleanup、Play、Recruit、Discard、Drawの5フェイズを順に行う。',20,'source_bound','fort:rule:five-phases','fort:binding:five-phases','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','fort:locator:five-phases','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'play-action','action','Playフェイズでは手札から1枚をプレイし、そのカードのpublic actionまたはprivate actionの一方または両方を解決できる。',30,'source_bound','fort:rule:play-action','fort:binding:play-action','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','fort:locator:play-action','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'follow','action','他プレイヤーは対応するsuitのカード1枚を捨てることで、プレイされたカードのpublic actionをfollowできる。',40,'source_bound','fort:rule:follow','fort:binding:follow','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','fort:locator:follow','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'recruit','action','RecruitフェイズではPark、他プレイヤーのYard、またはPark deckの上からカード1枚を必ず勧誘する。',50,'source_bound','fort:rule:recruit','fort:binding:recruit','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','fort:locator:recruit','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'end-trigger','condition','誰かが25VP以上に到達する、Fort Level 5に到達する、またはPark deckが尽きるとゲーム終了がトリガーされる。',60,'source_bound','fort:rule:end-trigger','fort:binding:end-trigger','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','fort:locator:end-trigger','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'final-score','victory','全員が同じ手番数を終えた後、VP track、Fort Level、Made-Up Rule、Macaroniの得点を合計し、最多VPが勝つ。',70,'source_bound','fort:rule:final-score','fort:binding:final-score','https://cdn.shopify.com/s/files/1/0106/0162/7706/files/Fort_Final_Rulebook_web_Oct_15_2020.pdf?v=1603136739','fort:locator:final-score','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'fort:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-batch-02"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('fort:binding:setup-deck','fort:rule:setup-deck','fort:leder-rulebook-2020-10-15','fort:locator:setup-deck','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('fort:binding:five-phases','fort:rule:five-phases','fort:leder-rulebook-2020-10-15','fort:locator:five-phases','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('fort:binding:play-action','fort:rule:play-action','fort:leder-rulebook-2020-10-15','fort:locator:play-action','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('fort:binding:follow','fort:rule:follow','fort:leder-rulebook-2020-10-15','fort:locator:follow','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('fort:binding:recruit','fort:rule:recruit','fort:leder-rulebook-2020-10-15','fort:locator:recruit','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('fort:binding:end-trigger','fort:rule:end-trigger','fort:leder-rulebook-2020-10-15','fort:locator:end-trigger','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('fort:binding:final-score','fort:rule:final-score','fort:leder-rulebook-2020-10-15','fort:locator:final-score','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 7
    THEN RAISE EXCEPTION 'RuleOps fort RuleNode count must be 7'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 7
    THEN RAISE EXCEPTION 'RuleOps fort Claim count must be 7'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 7
    THEN RAISE EXCEPTION 'RuleOps fort EvidenceBinding count must be 7'; END IF;
END $$;

-- RuleOps game: papayoo / Gigamic Papayoo US rules 08-2024 / gigamic-papayoo-us-rules-08-2024-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('papayoo:gigamic-product','https://en.gigamic.com/games-for-fun/84-papayoo.html','Papayoo — publisher_product_page','publisher_product_page',NULL,'physical','ja','current product page accessed 2026-08-26','{"authority":"publisher_product_page","ruleops":true,"scope":"Papayoo base game (Gigamic, rules 08-2024)"}'::jsonb),
('papayoo:gigamic-rules-08-2024','https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf','Papayoo — publisher_rulebook','publisher_rulebook',NULL,'physical','ja','08-2024','{"authority":"publisher_rulebook","ruleops":true,"scope":"Papayoo base game (Gigamic, rules 08-2024)"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('papayoo:locator:goal-low-score','papayoo:gigamic-rules-08-2024','Goal of the Game','Goal of the Game'),
('papayoo:locator:setup-deck','papayoo:gigamic-rules-08-2024','Setup','Setup'),
('papayoo:locator:pass-left','papayoo:gigamic-rules-08-2024','Setup: Pass cards to the player on your left','Setup: Pass cards to the player on your left'),
('papayoo:locator:determine-papayoo','papayoo:gigamic-rules-08-2024','Setup: Determine the Papayoo','Setup: Determine the Papayoo'),
('papayoo:locator:follow-suit','papayoo:gigamic-rules-08-2024','Playing a Round: Tricks','Playing a Round: Tricks'),
('papayoo:locator:penalty-score','papayoo:gigamic-rules-08-2024','Goal of the Game / Card values','Goal of the Game / Card values')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='papayoo' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game papayoo absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for papayoo'; END IF;

  UPDATE public.games SET
    title='Papayoo',
    identity_status='verified', identity_source='https://en.gigamic.com/games-for-fun/84-papayoo.html',
    source_url='https://en.gigamic.com/games-for-fun/84-papayoo.html', source_trust='official_publisher',
    content_review_status='review_required', is_official=true,
    edition_label='Gigamic Papayoo US rules 08-2024', language_code='ja',
    source_revision='gigamic-papayoo-us-rules-08-2024-accessed-2026-08-26', updated_at=now(), rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Gigamic Papayoo US rules 08-2024'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='gigamic-papayoo-us-rules-08-2024-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','Gigamic Papayoo US rules 08-2024',
      'gigamic-papayoo-us-rules-08-2024-accessed-2026-08-26',true,'gigamic-papayoo-us-rules-08-2024-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['papayoo:gigamic-product','papayoo:gigamic-rules-08-2024']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='gigamic-papayoo-us-rules-08-2024-accessed-2026-08-26',source_ids=ARRAY['papayoo:gigamic-product','papayoo:gigamic-rules-08-2024']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'goal-low-score','victory','ゲーム終了時の累積得点が最も少ないプレイヤーが勝つ。',10,'source_bound','papayoo:rule:goal-low-score','papayoo:binding:goal-low-score','https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf','papayoo:locator:goal-low-score','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'setup-deck','setup','60枚を混ぜて配り、7人または8人では通常4スートの1を除いて56枚でプレイする。',20,'source_bound','papayoo:rule:setup-deck','papayoo:binding:setup-deck','https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf','papayoo:locator:setup-deck','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'pass-left','setup','配札後、人数に応じた枚数を左隣へ伏せて渡し、右隣から受け取る前に渡すカードを決める。',30,'source_bound','papayoo:rule:pass-left','papayoo:binding:pass-left','https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf','papayoo:locator:pass-left','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'determine-papayoo','setup','ディーラーが8面ダイスを振り、そのスートの7をそのラウンドのPapayooとする。',40,'source_bound','papayoo:rule:determine-papayoo','papayoo:binding:determine-papayoo','https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf','papayoo:locator:determine-papayoo','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'follow-suit','turn','トリックではリードされたスートを持っていれば同じスートを出し、持っていなければ任意のカードを出せる。',50,'source_bound','papayoo:rule:follow-suit','papayoo:binding:follow-suit','https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf','papayoo:locator:follow-suit','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'penalty-score','scoring','獲得したPayooカードは表示値が失点となり、そのラウンドのPapayooは40点、その他のカードは0点として数える。',60,'source_bound','papayoo:rule:penalty-score','papayoo:binding:penalty-score','https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf','papayoo:locator:penalty-score','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'papayoo:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-batch-02"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('papayoo:binding:goal-low-score','papayoo:rule:goal-low-score','papayoo:gigamic-rules-08-2024','papayoo:locator:goal-low-score','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('papayoo:binding:setup-deck','papayoo:rule:setup-deck','papayoo:gigamic-rules-08-2024','papayoo:locator:setup-deck','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('papayoo:binding:pass-left','papayoo:rule:pass-left','papayoo:gigamic-rules-08-2024','papayoo:locator:pass-left','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('papayoo:binding:determine-papayoo','papayoo:rule:determine-papayoo','papayoo:gigamic-rules-08-2024','papayoo:locator:determine-papayoo','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('papayoo:binding:follow-suit','papayoo:rule:follow-suit','papayoo:gigamic-rules-08-2024','papayoo:locator:follow-suit','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('papayoo:binding:penalty-score','papayoo:rule:penalty-score','papayoo:gigamic-rules-08-2024','papayoo:locator:penalty-score','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 6
    THEN RAISE EXCEPTION 'RuleOps papayoo RuleNode count must be 6'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 6
    THEN RAISE EXCEPTION 'RuleOps papayoo Claim count must be 6'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 6
    THEN RAISE EXCEPTION 'RuleOps papayoo EvidenceBinding count must be 6'; END IF;
END $$;

-- RuleOps game: forest-shuffle / Lookout Forest Shuffle base game 2023 / current official rules / lookout-forest-shuffle-base-rules-current-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('forest-shuffle:lookout-product','https://www.lookout-spiele.de/en/games/forrestshuffle.html','Forest Shuffle — publisher_product_page','publisher_product_page',NULL,'physical','ja','current base product page accessed 2026-08-26','{"authority":"publisher_product_page","ruleops":true,"scope":"Forest Shuffle base game (Lookout, 2023)"}'::jsonb),
('forest-shuffle:lookout-rulebook','https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf','Forest Shuffle — publisher_rulebook','publisher_rulebook',NULL,'physical','ja','current official base rules indexed 2026-08-26','{"authority":"publisher_rulebook","ruleops":true,"scope":"Forest Shuffle base game (Lookout, 2023)"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('forest-shuffle:locator:build-forest','forest-shuffle:lookout-rulebook','Overview / End of Game','Overview / End of Game'),
('forest-shuffle:locator:play-card-cost','forest-shuffle:lookout-rulebook','Playing a Card','Playing a Card'),
('forest-shuffle:locator:tree-slots','forest-shuffle:lookout-rulebook','Trees / Animals, Plants, and Mushrooms','Trees / Animals, Plants, and Mushrooms'),
('forest-shuffle:locator:tree-reveal','forest-shuffle:lookout-rulebook','Trees','Trees'),
('forest-shuffle:locator:third-winter-end','forest-shuffle:lookout-rulebook','End of Game','End of Game'),
('forest-shuffle:locator:highest-score-wins','forest-shuffle:lookout-rulebook','End of Game / Scoring','End of Game / Scoring')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='forest-shuffle' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game forest-shuffle absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for forest-shuffle'; END IF;

  UPDATE public.games SET
    title='Forest Shuffle',
    identity_status='verified', identity_source='https://www.lookout-spiele.de/en/games/forrestshuffle.html',
    source_url='https://www.lookout-spiele.de/en/games/forrestshuffle.html', source_trust='official_publisher',
    content_review_status='review_required', is_official=true,
    edition_label='Lookout Forest Shuffle base game 2023 / current official rules', language_code='ja',
    source_revision='lookout-forest-shuffle-base-rules-current-accessed-2026-08-26', updated_at=now(), rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Lookout Forest Shuffle base game 2023 / current official rules'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='lookout-forest-shuffle-base-rules-current-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','Lookout Forest Shuffle base game 2023 / current official rules',
      'lookout-forest-shuffle-base-rules-current-accessed-2026-08-26',true,'lookout-forest-shuffle-base-rules-current-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['forest-shuffle:lookout-product','forest-shuffle:lookout-rulebook']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='lookout-forest-shuffle-base-rules-current-accessed-2026-08-26',source_ids=ARRAY['forest-shuffle:lookout-product','forest-shuffle:lookout-rulebook']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'build-forest','victory','プレイヤーは木と生物を自分の森へ配置し、ゲーム終了時に最も高い得点を得ることを目指す。',10,'source_bound','forest-shuffle:rule:build-forest','forest-shuffle:binding:build-forest','https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf','forest-shuffle:locator:build-forest','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'play-card-cost','action','手札からカードをプレイする場合、カードのコスト分の別カードを手札から表向きでclearingへ置いて支払う。',20,'source_bound','forest-shuffle:rule:play-card-cost','forest-shuffle:binding:play-card-cost','https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf','forest-shuffle:locator:play-card-cost','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'tree-slots','effect','木は上下左右にsplit card用の4つのスロットを持ち、split cardは対応する側の空きスロットへ配置する。',30,'source_bound','forest-shuffle:rule:tree-slots','forest-shuffle:binding:tree-slots','https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf','forest-shuffle:locator:tree-slots','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'tree-reveal','effect','木をプレイするたびに山札の一番上のカード1枚を表向きでclearingへ置く。',40,'source_bound','forest-shuffle:rule:tree-reveal','forest-shuffle:binding:tree-reveal','https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf','forest-shuffle:locator:tree-reveal','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'third-winter-end','condition','3枚目のwinter cardが公開されると手番を完了せず即座にゲームを終了し、得点計算へ進む。',50,'source_bound','forest-shuffle:rule:third-winter-end','forest-shuffle:binding:third-winter-end','https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf','forest-shuffle:locator:third-winter-end','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'highest-score-wins','victory','森の見えているカードの得点とcave内カードの得点を合計し、最も高い得点のプレイヤーが勝つ。',60,'source_bound','forest-shuffle:rule:highest-score-wins','forest-shuffle:binding:highest-score-wins','https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf','forest-shuffle:locator:highest-score-wins','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'forest-shuffle:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-batch-02"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('forest-shuffle:binding:build-forest','forest-shuffle:rule:build-forest','forest-shuffle:lookout-rulebook','forest-shuffle:locator:build-forest','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('forest-shuffle:binding:play-card-cost','forest-shuffle:rule:play-card-cost','forest-shuffle:lookout-rulebook','forest-shuffle:locator:play-card-cost','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('forest-shuffle:binding:tree-slots','forest-shuffle:rule:tree-slots','forest-shuffle:lookout-rulebook','forest-shuffle:locator:tree-slots','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('forest-shuffle:binding:tree-reveal','forest-shuffle:rule:tree-reveal','forest-shuffle:lookout-rulebook','forest-shuffle:locator:tree-reveal','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('forest-shuffle:binding:third-winter-end','forest-shuffle:rule:third-winter-end','forest-shuffle:lookout-rulebook','forest-shuffle:locator:third-winter-end','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now()),
('forest-shuffle:binding:highest-score-wins','forest-shuffle:rule:highest-score-wins','forest-shuffle:lookout-rulebook','forest-shuffle:locator:highest-score-wins','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-batch-02"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 6
    THEN RAISE EXCEPTION 'RuleOps forest-shuffle RuleNode count must be 6'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 6
    THEN RAISE EXCEPTION 'RuleOps forest-shuffle Claim count must be 6'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 6
    THEN RAISE EXCEPTION 'RuleOps forest-shuffle EvidenceBinding count must be 6'; END IF;
END $$;

COMMIT;
