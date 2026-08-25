BEGIN;

-- Canonical scope: アークライト『タイムボム』2017年11月24日発売のリニューアル版。
-- 2014原版、タイムボム2、HIDEOUT、タイムボムQは別製品・別revisionとして混在させない。
-- 公式商品ページで直接確認できない詳細なセットアップ、ラウンド進行、勝敗処理は推測せず公開authorityから除外する。
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'publisher:arclight:time-bomb:2017-product',
  'https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/',
  'タイムボム — ArclightGames Official product page',
  'publisher_product','アークライト','physical','ja','2017-11-24-product',
  '{"authority":"publisher_product","audit_date":"2026-08-25","scope":"identity_players_time_age_components_core_goal_optional_third_faction"}'::jsonb
),
(
  'publisher:kadokawa:time-bomb-q:2025-history',
  'https://group.kadokawa.co.jp/information/promotional_topics/article-12783.html',
  'タイムボムQ発売告知 — KADOKAWAグループ（タイムボム製品史）',
  'publisher_press_release','KADOKAWA / アークライト','physical','ja','2025-07-25-history',
  '{"authority":"publisher_press_release","audit_date":"2026-08-25","scope":"2014_original_vs_2017_arclight_renewal_vs_2025_timebomb_q_boundary"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('time-bomb:arclight:identity','publisher:arclight:time-bomb:2017-product',NULL,'「タイムボム」商品概要','2017年11月24日発売、2〜8人、1〜30分、10歳以上、アークライト版'),
('time-bomb:arclight:goal','publisher:arclight:time-bomb:2017-product',NULL,'どんなゲーム？','時間を巻き戻してしまうタイムボムの爆発を阻止する正体隠匿ゲーム'),
('time-bomb:arclight:third-faction','publisher:arclight:time-bomb:2017-product',NULL,'どんなゲーム？','追加選択ルールとして第三陣営が存在する'),
('time-bomb:kadokawa:edition-boundary','publisher:kadokawa:time-bomb-q:2025-history',NULL,'「タイムボム」とは？','2014年原版、2017年11月24日アークライトのリニューアル版、2025年タイムボムQを区別')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='time-bomb' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Time Bomb canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Time Bomb Work row is required'; END IF;

  UPDATE public.games SET
    title='Time Bomb',title_ja='タイムボム',title_en='Time Bomb',
    description='時空警察とボマー団の思惑が交錯する、脱落なしの正体隠匿カードゲーム。2017年にアークライトからリニューアル版として発売。',
    summary='タイムボムの爆発阻止をめぐる心理戦を楽しむ。第三陣営は追加選択ルールとして基本ルールと分離する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/',
    source_url='https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/',
    official_url='https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='アークライト リニューアル版（2017）',language_code='ja',publisher='アークライト',published_year=2017,
    source_revision='Arclight official 2017-11-24 product identity; detailed rulebook not directly verified; audited 2026-08-25',
    min_players=2,max_players=8,play_time=30,min_age=10,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='アークライト リニューアル版（2017）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='arclight-2017-core'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','アークライト リニューアル版（2017）',
      'Arclight official 2017-11-24 product identity; detailed rulebook not directly verified; audited 2026-08-25',
      true,'arclight-2017-core','physical','アークライト','active','source_bound',
      ARRAY['publisher:arclight:time-bomb:2017-product','publisher:kadokawa:time-bomb-q:2025-history']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Arclight official 2017-11-24 product identity; detailed rulebook not directly verified; audited 2026-08-25',
      publisher_name='アークライト',status='active',verification_status='source_bound',
      source_ids=ARRAY['publisher:arclight:time-bomb:2017-product','publisher:kadokawa:time-bomb-q:2025-history']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'objective.prevent_explosion','victory','タイムボムの爆発を阻止することがゲームの基本目標として示されている。',10,'source_bound','time-bomb:rule:objective.prevent_explosion','time-bomb:binding:objective.prevent_explosion','https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/','time-bomb:arclight:goal','{}'::jsonb),
  (v_ruleset_id,'variant.optional_third_faction','condition','第三陣営は追加選択ルールであり、基本ゲームへ必須要素として混在させない。',20,'source_bound','time-bomb:rule:variant.optional_third_faction','time-bomb:binding:variant.optional_third_faction','https://arclightgames.jp/product/%E3%82%BF%E3%82%A4%E3%83%A0%E3%83%9C%E3%83%A0/','time-bomb:arclight:third-faction','{"scope":"optional_variant_boundary"}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'time-bomb:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_source_normalization","audit_date":"2026-08-25","scope":"time_bomb_arclight_2017_core"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'time-bomb:binding:'||rn.rule_id,'time-bomb:rule:'||rn.rule_id,'publisher:arclight:time-bomb:2017-product',
    rn.source_locator,'supports','{"review":"publisher_product"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 2 THEN RAISE EXCEPTION 'Time Bomb source-bound RuleNode count must be 2'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 2 THEN RAISE EXCEPTION 'Time Bomb accepted Claim count must be 2'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 2 THEN RAISE EXCEPTION 'Time Bomb supporting EvidenceBinding count must be 2'; END IF;
END $$;

COMMIT;