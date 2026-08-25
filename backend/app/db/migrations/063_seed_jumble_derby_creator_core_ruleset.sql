BEGIN;

-- Canonical scope: ララチラゲームズ『ジャンブルダービー』2023秋版の通常ルール。
-- 作者公式のGame Market掲載とBOOTH商品説明で直接確認できる、安定したコアだけを正規化する。
-- 詳細なセットアップ、レース進行、得点、終了処理は一次ルール本文が確認できるまで推測しない。
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'creator:lalachira:jumble-derby:gamemarket',
  'https://gamemarket.jp/game/181906',
  'ジャンブルダービー — ララチラゲームズ Game Market公式掲載',
  'creator_listing','ララチラゲームズ','physical','ja','2023-autumn-listing',
  '{"authority":"creator_listing","audit_date":"2026-08-25","scope":"identity_players_time_age_core_gameplay_duel_boundary"}'::jsonb
),
(
  'creator:lalachira:jumble-derby:booth',
  'https://booth.pm/ja/items/5338090',
  'ジャンブルダービー — lalachira-games BOOTH公式商品ページ',
  'creator_storefront','ララチラゲームズ','physical','ja','current-storefront',
  '{"authority":"creator_storefront","audit_date":"2026-08-25","scope":"identity_players_time_age_core_gameplay"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,page_number,section_heading,external_reference) VALUES
('jumble-derby:gamemarket:identity','creator:lalachira:jumble-derby:gamemarket',NULL,'ゲーム概要','3–5人、45–90分、10歳以上、2023秋、ララチラゲームズ'),
('jumble-derby:gamemarket:board-hand','creator:lalachira:jumble-derby:gamemarket',NULL,'ゲームのコンセプト','プレイボード上のコマの位置取りと手札のカードを組み合わせた駆け引き'),
('jumble-derby:gamemarket:shared-deck','creator:lalachira:jumble-derby:gamemarket',NULL,'ゲームのコンセプト','通常ゲームでは共有の山札を使用する'),
('jumble-derby:gamemarket:goal','creator:lalachira:jumble-derby:gamemarket',NULL,'ゲーム概要','馬の能力やキャラクターカードなどを駆使して自分の馬を勝利に導く'),
('jumble-derby:gamemarket:duel','creator:lalachira:jumble-derby:gamemarket',NULL,'デュエルモードについて','製品所有者同士で遊ぶ別モード。40枚デッキ等を用い、その他の進行・勝利条件は通常ルールと同じ'),
('jumble-derby:booth:identity','creator:lalachira:jumble-derby:booth',NULL,'レギュレーション','3–5人（推奨4人）、45–90分、10歳以上')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,page_number=EXCLUDED.page_number,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_game_id uuid; v_work_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id,work_id INTO v_game_id,v_work_id FROM public.games WHERE slug='jumble-derby' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Jumble Derby canonical game row not present in this fixture; skipping catalog-bound seed';
    RETURN;
  END IF;
  IF v_work_id IS NULL THEN RAISE EXCEPTION 'Canonical Jumble Derby Work row is required'; END IF;

  UPDATE public.games SET
    title='Jumble Derby',title_ja='ジャンブルダービー',title_en='Jumble Derby',
    description='馬の能力やキャラクターカード、ボード上の位置取りと手札を組み合わせ、自分の馬を勝利へ導く3～5人用の戦略型レースゲーム。',
    summary='通常ルールでは共有の山札を使い、ボード上の位置取りと手札のカードを組み合わせて自分の馬の勝利を目指す。デュエルモードは別バリアントとして分離する。',
    rules='{}'::jsonb,rules_content=NULL,structured_data='{}'::jsonb,setup_summary=NULL,gameplay_summary=NULL,end_game_summary=NULL,
    identity_status='verified',identity_source='https://gamemarket.jp/game/181906',
    source_url='https://gamemarket.jp/game/181906',official_url='https://booth.pm/ja/items/5338090',
    source_trust='official_publisher',content_review_status='review_required',is_official=true,
    edition_label='ジャンブルダービー（2023秋版）',language_code='ja',publisher='ララチラゲームズ',
    source_revision='Creator Game Market 2023秋 listing and current BOOTH storefront; stable core only; detailed normal rules remain unverified; audited 2026-08-25',
    min_players=3,max_players=5,play_time=90,min_age=10,updated_at=now()
  WHERE id=v_game_id;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='ジャンブルダービー（2023秋版）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='creator-core-2023-autumn'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets(
      game_id,work_id,version,schema_version,language_code,edition_label,source_revision,is_active,
      revision_label,platform,publisher_name,status,verification_status,source_ids
    ) VALUES(
      v_game_id,v_work_id,1,'1.0','ja','ジャンブルダービー（2023秋版）',
      'Creator Game Market 2023秋 listing and current BOOTH storefront; stable core only; detailed normal rules remain unverified; audited 2026-08-25',
      true,'creator-core-2023-autumn','physical','ララチラゲームズ','active','source_bound',
      ARRAY['creator:lalachira:jumble-derby:gamemarket','creator:lalachira:jumble-derby:booth']::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET work_id=v_work_id,schema_version='1.0',is_active=true,
      source_revision='Creator Game Market 2023秋 listing and current BOOTH storefront; stable core only; detailed normal rules remain unverified; audited 2026-08-25',
      publisher_name='ララチラゲームズ',status='active',verification_status='source_bound',
      source_ids=ARRAY['creator:lalachira:jumble-derby:gamemarket','creator:lalachira:jumble-derby:booth']::text[],updated_at=now()
    WHERE id=v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'setup.shared_deck','setup','通常ルールでは、プレイヤー共通の山札を使用する。',10,'source_bound','jumble-derby:rule:setup.shared_deck','jumble-derby:binding:setup.shared_deck','https://gamemarket.jp/game/181906','jumble-derby:gamemarket:shared-deck','{}'::jsonb),
  (v_ruleset_id,'action.board_hand_tactics','action','プレイボード上のコマの位置取りと、手札のカードを組み合わせてレースを進める。',20,'source_bound','jumble-derby:rule:action.board_hand_tactics','jumble-derby:binding:action.board_hand_tactics','https://gamemarket.jp/game/181906','jumble-derby:gamemarket:board-hand','{}'::jsonb),
  (v_ruleset_id,'victory.lead_horse','victory','馬の能力やキャラクターカードなどを使い、自分の馬を勝利へ導くことを目指す。',30,'source_bound','jumble-derby:rule:victory.lead_horse','jumble-derby:binding:victory.lead_horse','https://gamemarket.jp/game/181906','jumble-derby:gamemarket:goal','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'jumble-derby:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"creator_source_normalization","audit_date":"2026-08-25","scope":"jumble_derby_2023_autumn_core"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at)
  SELECT 'jumble-derby:binding:'||rn.rule_id,'jumble-derby:rule:'||rn.rule_id,'creator:lalachira:jumble-derby:gamemarket',
    rn.source_locator,'supports','{"review":"creator_listing"}'::jsonb,'{}'::jsonb,now()
  FROM public.rule_nodes rn WHERE rn.rule_set_id=v_ruleset_id
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 3 THEN RAISE EXCEPTION 'Jumble Derby source-bound RuleNode count must be 3'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 3 THEN RAISE EXCEPTION 'Jumble Derby accepted Claim count must be 3'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 3 THEN RAISE EXCEPTION 'Jumble Derby supporting EvidenceBinding count must be 3'; END IF;
END $$;

COMMIT;
