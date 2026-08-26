BEGIN;

-- RuleOps game: ice-fall / Smart Ape Games 2025 Japanese edition / smart-ape-2025-05-13-rules-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('ice-fall:creator-listing-2025','https://gamemarket.jp/game/184994/','ICE FALL — creator_listing','creator_listing',NULL,'physical','ja','2025 product listing','{"authority":"creator_listing","ruleops":true,"scope":"ICE FALL / アイスフォール (Smart Ape Games, 2025)"}'::jsonb),
('ice-fall:creator-rules-2025-05-13','https://gamemarket.jp/blog/193416','ICE FALL — creator_rulebook','creator_rulebook',NULL,'physical','ja','2025-05-13 creator rule explanation','{"authority":"creator_rulebook","ruleops":true,"scope":"ICE FALL / アイスフォール (Smart Ape Games, 2025)"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('ice-fall:locator:goal-summit','ice-fall:creator-rules-2025-05-13','ゲーム概要：兄弟コマで氷壁の頂上を目指す','ゲーム概要：兄弟コマで氷壁の頂上を目指す'),
('ice-fall:locator:choose-brother','ice-fall:creator-rules-2025-05-13','大まかなルール：1ターンで登らせられるのは兄か弟のどちらか','大まかなルール：1ターンで登らせられるのは兄か弟のどちらか'),
('ice-fall:locator:declare-and-card','ice-fall:creator-rules-2025-05-13','大まかなルール：1〜10のカードを伏せて兄/弟を宣言','大まかなルール：1〜10のカードを伏せて兄/弟を宣言'),
('ice-fall:locator:compare-declarations','ice-fall:creator-rules-2025-05-13','大まかなルール：同じ宣言ごとに数字を比較して移動','大まかなルール：同じ宣言ごとに数字を比較して移動'),
('ice-fall:locator:round-five-cards','ice-fall:creator-rules-2025-05-13','大まかな流れ：歩数カードを5枚処理したら1ラウンド終了','大まかな流れ：歩数カードを5枚処理したら1ラウンド終了')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='ice-fall' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game ice-fall absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for ice-fall'; END IF;

  UPDATE public.games SET
    title='ICE FALL',
    identity_status='verified', identity_source='https://gamemarket.jp/game/184994/',
    source_url='https://gamemarket.jp/game/184994/', source_trust='authorized_partner',
    content_review_status='review_required', is_official=true,
    edition_label='Smart Ape Games 2025 Japanese edition', language_code='ja',
    source_revision='smart-ape-2025-05-13-rules-accessed-2026-08-26', updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Smart Ape Games 2025 Japanese edition'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='smart-ape-2025-05-13-rules-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','Smart Ape Games 2025 Japanese edition',
      'smart-ape-2025-05-13-rules-accessed-2026-08-26',true,'smart-ape-2025-05-13-rules-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['ice-fall:creator-listing-2025','ice-fall:creator-rules-2025-05-13']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='smart-ape-2025-05-13-rules-accessed-2026-08-26',source_ids=ARRAY['ice-fall:creator-listing-2025','ice-fall:creator-rules-2025-05-13']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'goal-summit','victory','自分の兄弟クライマーを氷壁の頂上まで登らせることを目指す。',10,'source_bound','ice-fall:rule:goal-summit','ice-fall:binding:goal-summit','https://gamemarket.jp/blog/193416','ice-fall:locator:goal-summit','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'choose-brother','turn','各ターンでは兄か弟のどちらか一方を登らせる。',20,'source_bound','ice-fall:rule:choose-brother','ice-fall:binding:choose-brother','https://gamemarket.jp/blog/193416','ice-fall:locator:choose-brother','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'declare-and-card','action','各プレイヤーは1〜10のカードを伏せ、兄と弟のどちらを登らせるか宣言する。',30,'source_bound','ice-fall:rule:declare-and-card','ice-fall:binding:declare-and-card','https://gamemarket.jp/blog/193416','ice-fall:locator:declare-and-card','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'compare-declarations','effect','同じ兄弟を宣言したプレイヤー同士でカードを公開し、最も大きい数字のプレイヤーは1位の歩数、それ以外は2位以下の歩数だけ対応するコマを進める。',40,'source_bound','ice-fall:rule:compare-declarations','ice-fall:binding:compare-declarations','https://gamemarket.jp/blog/193416','ice-fall:locator:compare-declarations','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'round-five-cards','round_end','歩数カードを5枚処理すると1ラウンドが終了する。',50,'source_bound','ice-fall:rule:round-five-cards','ice-fall:binding:round-five-cards','https://gamemarket.jp/blog/193416','ice-fall:locator:round-five-cards','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'ice-fall:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-pilot-01"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('ice-fall:binding:goal-summit','ice-fall:rule:goal-summit','ice-fall:creator-rules-2025-05-13','ice-fall:locator:goal-summit','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('ice-fall:binding:choose-brother','ice-fall:rule:choose-brother','ice-fall:creator-rules-2025-05-13','ice-fall:locator:choose-brother','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('ice-fall:binding:declare-and-card','ice-fall:rule:declare-and-card','ice-fall:creator-rules-2025-05-13','ice-fall:locator:declare-and-card','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('ice-fall:binding:compare-declarations','ice-fall:rule:compare-declarations','ice-fall:creator-rules-2025-05-13','ice-fall:locator:compare-declarations','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('ice-fall:binding:round-five-cards','ice-fall:rule:round-five-cards','ice-fall:creator-rules-2025-05-13','ice-fall:locator:round-five-cards','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 5
    THEN RAISE EXCEPTION 'RuleOps ice-fall RuleNode count must be 5'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 5
    THEN RAISE EXCEPTION 'RuleOps ice-fall Claim count must be 5'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 5
    THEN RAISE EXCEPTION 'RuleOps ice-fall EvidenceBinding count must be 5'; END IF;
END $$;

-- RuleOps game: slide / Gigamic English rulebook 01-2024 / gigamic-slide-rulebook-01-2024-attachment-548-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('slide:gigamic-product','https://en.gigamic.com/family-games/1211-slide.html','Slide — publisher_product_page','publisher_product_page',NULL,'physical','ja','current product page','{"authority":"publisher_product_page","ruleops":true,"scope":"Slide (Gigamic, rulebook 01-2024)"}'::jsonb),
('slide:gigamic-rulebook-01-2024','https://en.gigamic.com/index.php?controller=attachment&id_attachment=548','Slide — publisher_rulebook','publisher_rulebook',NULL,'physical','ja','01-2024','{"authority":"publisher_rulebook","ruleops":true,"scope":"Slide (Gigamic, rulebook 01-2024)"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('slide:locator:setup-grid','slide:gigamic-rulebook-01-2024','p.1 Setup','p.1 Setup'),
('slide:locator:reveal-one','slide:gigamic-rulebook-01-2024','p.1 Playing the game','p.1 Playing the game'),
('slide:locator:slide-card','slide:gigamic-rulebook-01-2024','p.2 Playing the game','p.2 Playing the game'),
('slide:locator:cancel-adjacent','slide:gigamic-rulebook-01-2024','p.2 End of the game','p.2 End of the game'),
('slide:locator:lowest-score-wins','slide:gigamic-rulebook-01-2024','p.2 End of the game','p.2 End of the game')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='slide' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game slide absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for slide'; END IF;

  UPDATE public.games SET
    title='Slide',
    identity_status='verified', identity_source='https://en.gigamic.com/family-games/1211-slide.html',
    source_url='https://en.gigamic.com/family-games/1211-slide.html', source_trust='official_publisher',
    content_review_status='review_required', is_official=true,
    edition_label='Gigamic English rulebook 01-2024', language_code='ja',
    source_revision='gigamic-slide-rulebook-01-2024-attachment-548-accessed-2026-08-26', updated_at=now(), rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='Gigamic English rulebook 01-2024'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='gigamic-slide-rulebook-01-2024-attachment-548-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','Gigamic English rulebook 01-2024',
      'gigamic-slide-rulebook-01-2024-attachment-548-accessed-2026-08-26',true,'gigamic-slide-rulebook-01-2024-attachment-548-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['slide:gigamic-product','slide:gigamic-rulebook-01-2024']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='gigamic-slide-rulebook-01-2024-attachment-548-accessed-2026-08-26',source_ids=ARRAY['slide:gigamic-product','slide:gigamic-rulebook-01-2024']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'setup-grid','setup','各プレイヤーに16枚を裏向きで配り、4×4のグリッドに並べる。',10,'source_bound','slide:rule:setup-grid','slide:binding:setup-grid','https://en.gigamic.com/index.php?controller=attachment&id_attachment=548','slide:locator:setup-grid','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'reveal-one','turn','各ラウンド、全員が自分のグリッドから裏向きカード1枚を選び、同時に中央へ表向きにする。',20,'source_bound','slide:rule:reveal-one','slide:binding:reveal-one','https://en.gigamic.com/index.php?controller=attachment&id_attachment=548','slide:locator:reveal-one','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'slide-card','action','中央から選んだカードは、空きマスを埋めて4×4へ戻すよう行または列の外側からスライドして入れ、斜めには動かさない。',30,'source_bound','slide:rule:slide-card','slide:binding:slide-card','https://en.gigamic.com/index.php?controller=attachment&id_attachment=548','slide:locator:slide-card','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'cancel-adjacent','scoring','全カード公開後、上下左右に隣接する同じ数字のカードは取り除く。',40,'source_bound','slide:rule:cancel-adjacent','slide:binding:cancel-adjacent','https://en.gigamic.com/index.php?controller=attachment&id_attachment=548','slide:locator:cancel-adjacent','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'lowest-score-wins','victory','残ったカードの数字を合計し、最も得点が少ないプレイヤーが勝つ。',50,'source_bound','slide:rule:lowest-score-wins','slide:binding:lowest-score-wins','https://en.gigamic.com/index.php?controller=attachment&id_attachment=548','slide:locator:lowest-score-wins','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'slide:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-pilot-01"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('slide:binding:setup-grid','slide:rule:setup-grid','slide:gigamic-rulebook-01-2024','slide:locator:setup-grid','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('slide:binding:reveal-one','slide:rule:reveal-one','slide:gigamic-rulebook-01-2024','slide:locator:reveal-one','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('slide:binding:slide-card','slide:rule:slide-card','slide:gigamic-rulebook-01-2024','slide:locator:slide-card','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('slide:binding:cancel-adjacent','slide:rule:cancel-adjacent','slide:gigamic-rulebook-01-2024','slide:locator:cancel-adjacent','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('slide:binding:lowest-score-wins','slide:rule:lowest-score-wins','slide:gigamic-rulebook-01-2024','slide:locator:lowest-score-wins','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 5
    THEN RAISE EXCEPTION 'RuleOps slide RuleNode count must be 5'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 5
    THEN RAISE EXCEPTION 'RuleOps slide Claim count must be 5'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 5
    THEN RAISE EXCEPTION 'RuleOps slide EvidenceBinding count must be 5'; END IF;
END $$;

-- RuleOps game: flip-7-with-a-vengeance / The Op RULESET EDITION 1 / the-op-ruleset-edition-1-copyright-2026-accessed-2026-08-26
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
('flip7-wav:product','https://theop.games/products/flip-7-with-a-vengeance','Flip 7: With A Vengeance — publisher_product_page','publisher_product_page',NULL,'physical','ja','2026 standalone sequel product page','{"authority":"publisher_product_page","ruleops":true,"scope":"Flip 7: With A Vengeance standalone sequel"}'::jsonb),
('flip7-wav:rulebook-ed1','https://cdn.shopify.com/s/files/1/0611/3958/3198/files/26_FLIP_7_VENGEANCE_RULES_C.pdf?v=1770853610','Flip 7: With A Vengeance — publisher_rulebook','publisher_rulebook',NULL,'physical','ja','RULESET EDITION 1 ©2026','{"authority":"publisher_rulebook","ruleops":true,"scope":"Flip 7: With A Vengeance standalone sequel"}'::jsonb),
('flip7-wav:faq','https://theop.games/pages/flip-7-wav-faqs','Flip 7: With A Vengeance — publisher_faq','publisher_faq',NULL,'physical','ja','current official FAQ accessed 2026-08-26','{"authority":"publisher_faq","ruleops":true,"scope":"Flip 7: With A Vengeance standalone sequel"}'::jsonb)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('flip-7-with-a-vengeance:locator:duplicate-bust','flip7-wav:rulebook-ed1','p.1 Overview / p.3 Important Terms','p.1 Overview / p.3 Important Terms'),
('flip-7-with-a-vengeance:locator:hit-or-stay','flip7-wav:rulebook-ed1','p.3 Important Terms / p.5 Playing a Round','p.3 Important Terms / p.5 Playing a Round'),
('flip-7-with-a-vengeance:locator:flip-seven','flip7-wav:rulebook-ed1','p.1 Overview / p.4 Playing a Round','p.1 Overview / p.4 Playing a Round'),
('flip-7-with-a-vengeance:locator:end-200','flip7-wav:rulebook-ed1','p.7 End of the Game','p.7 End of the Game'),
('flip-7-with-a-vengeance:locator:flip-four-bust','flip7-wav:faq','FAQ: Order of operations for a Flip Four with Actions','FAQ: Order of operations for a Flip Four with Actions'),
('flip-7-with-a-vengeance:locator:action-required','flip7-wav:faq','FAQ: Do you HAVE to use an Action card?','FAQ: Do you HAVE to use an Action card?')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='flip-7-with-a-vengeance' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE NOTICE 'RuleOps game flip-7-with-a-vengeance absent; skipping'; RETURN; END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Work row is required for flip-7-with-a-vengeance'; END IF;

  UPDATE public.games SET
    title='Flip 7: With A Vengeance',
    identity_status='verified', identity_source='https://theop.games/products/flip-7-with-a-vengeance',
    source_url='https://theop.games/products/flip-7-with-a-vengeance', source_trust='official_publisher',
    content_review_status='review_required', is_official=true,
    edition_label='The Op RULESET EDITION 1', language_code='ja',
    source_revision='the-op-ruleset-edition-1-copyright-2026-accessed-2026-08-26', updated_at=now(), rules='{}'::jsonb, rules_content=NULL, structured_data='{}'::jsonb, setup_summary=NULL, gameplay_summary=NULL, end_game_summary=NULL
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='The Op RULESET EDITION 1'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='the-op-ruleset-edition-1-copyright-2026-accessed-2026-08-26'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','The Op RULESET EDITION 1',
      'the-op-ruleset-edition-1-copyright-2026-accessed-2026-08-26',true,'the-op-ruleset-edition-1-copyright-2026-accessed-2026-08-26','physical',NULL,
      'active','source_bound',ARRAY['flip7-wav:product','flip7-wav:rulebook-ed1','flip7-wav:faq']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id=v_work_id,is_active=true,status='active',verification_status='source_bound',
      source_revision='the-op-ruleset-edition-1-copyright-2026-accessed-2026-08-26',source_ids=ARRAY['flip7-wav:product','flip7-wav:rulebook-ed1','flip7-wav:faq']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
(v_ruleset_id,'duplicate-bust','condition','自分の列にすでにある数字と同じNumber cardをもう1枚引くとBustし、そのラウンドは得点しない。',10,'source_bound','flip-7-with-a-vengeance:rule:duplicate-bust','flip-7-with-a-vengeance:binding:duplicate-bust','https://cdn.shopify.com/s/files/1/0611/3958/3198/files/26_FLIP_7_VENGEANCE_RULES_C.pdf?v=1770853610','flip-7-with-a-vengeance:locator:duplicate-bust','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'hit-or-stay','turn','アクティブなプレイヤーはHitでカードを受け取るか、Stayして以後自分からカードを受け取らないかを選ぶ。',20,'source_bound','flip-7-with-a-vengeance:rule:hit-or-stay','flip-7-with-a-vengeance:binding:hit-or-stay','https://cdn.shopify.com/s/files/1/0611/3958/3198/files/26_FLIP_7_VENGEANCE_RULES_C.pdf?v=1770853610','flip-7-with-a-vengeance:locator:hit-or-stay','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'flip-seven','round_end','異なるNumber cardを7枚そろえるとFlip 7となり、ラウンドは即時終了して15点のボーナスを得る。',30,'source_bound','flip-7-with-a-vengeance:rule:flip-seven','flip-7-with-a-vengeance:binding:flip-seven','https://cdn.shopify.com/s/files/1/0611/3958/3198/files/26_FLIP_7_VENGEANCE_RULES_C.pdf?v=1770853610','flip-7-with-a-vengeance:locator:flip-seven','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'end-200','victory','ラウンド終了時に1人以上が200点以上ならゲームを終了し、その時点で合計得点が最も高いプレイヤーが勝つ。',40,'source_bound','flip-7-with-a-vengeance:rule:end-200','flip-7-with-a-vengeance:binding:end-200','https://cdn.shopify.com/s/files/1/0611/3958/3198/files/26_FLIP_7_VENGEANCE_RULES_C.pdf?v=1770853610','flip-7-with-a-vengeance:locator:end-200','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'flip-four-bust','effect','Flip Four中は1枚ずつ最大4枚まで公開し、重複数字でBustしたら直ちに停止し、そのFlip Four中に出たAction cardでBustを救済できない。',50,'source_bound','flip-7-with-a-vengeance:rule:flip-four-bust','flip-7-with-a-vengeance:binding:flip-four-bust','https://theop.games/pages/flip-7-wav-faqs','flip-7-with-a-vengeance:locator:flip-four-bust','{"ruleops_batch":true}'::jsonb),
(v_ruleset_id,'action-required','condition','Action cardは有効な対象がある場合は使用しなければならず、有効な対象がない場合は捨てる。',60,'source_bound','flip-7-with-a-vengeance:rule:action-required','flip-7-with-a-vengeance:binding:action-required','https://theop.games/pages/flip-7-wav-faqs','flip-7-with-a-vengeance:locator:action-required','{"ruleops_batch":true}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT 'flip-7-with-a-vengeance:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted',
    '{"method":"ruleops_reviewed_manifest","batch_id":"2026-08-26-pilot-01"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
('flip-7-with-a-vengeance:binding:duplicate-bust','flip-7-with-a-vengeance:rule:duplicate-bust','flip7-wav:rulebook-ed1','flip-7-with-a-vengeance:locator:duplicate-bust','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('flip-7-with-a-vengeance:binding:hit-or-stay','flip-7-with-a-vengeance:rule:hit-or-stay','flip7-wav:rulebook-ed1','flip-7-with-a-vengeance:locator:hit-or-stay','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('flip-7-with-a-vengeance:binding:flip-seven','flip-7-with-a-vengeance:rule:flip-seven','flip7-wav:rulebook-ed1','flip-7-with-a-vengeance:locator:flip-seven','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('flip-7-with-a-vengeance:binding:end-200','flip-7-with-a-vengeance:rule:end-200','flip7-wav:rulebook-ed1','flip-7-with-a-vengeance:locator:end-200','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('flip-7-with-a-vengeance:binding:flip-four-bust','flip-7-with-a-vengeance:rule:flip-four-bust','flip7-wav:faq','flip-7-with-a-vengeance:locator:flip-four-bust','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now()),
('flip-7-with-a-vengeance:binding:action-required','flip-7-with-a-vengeance:rule:action-required','flip7-wav:faq','flip-7-with-a-vengeance:locator:action-required','supports','{"review":"ruleops_reviewed_manifest"}'::jsonb,'{"batch_id":"2026-08-26-pilot-01"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 6
    THEN RAISE EXCEPTION 'RuleOps flip-7-with-a-vengeance RuleNode count must be 6'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 6
    THEN RAISE EXCEPTION 'RuleOps flip-7-with-a-vengeance Claim count must be 6'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 6
    THEN RAISE EXCEPTION 'RuleOps flip-7-with-a-vengeance EvidenceBinding count must be 6'; END IF;
END $$;

COMMIT;
