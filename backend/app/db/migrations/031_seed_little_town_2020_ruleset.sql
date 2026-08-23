BEGIN;

-- Little Town Builders physical Japanese remake sold by Arclight from 2020.
-- Product identity and localized metadata are bound to Arclight's official product page.
-- Core rules are normalized from IELLO's official 2019 Little Town rulebook and
-- cross-checked against Studio GG's first-party description of the original design.
-- Arclight-only additional building tiles/maps are treated as content additions, not
-- permission to import unrelated variants; claims below are limited to shared base play.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:arclight:little-town:2020-product',
    'https://arclightgames.jp/product/%E3%83%AA%E3%83%88%E3%83%AB%E3%82%BF%E3%82%A6%E3%83%B3%E3%83%93%E3%83%AB%E3%83%80%E3%83%BC%E3%82%BA/',
    'Arclight リトルタウンビルダーズ official product page',
    'publisher_product_page',
    'Arclight',
    'physical',
    'ja',
    '2020-01-23',
    '{"authority":"publisher","role":"canonical_japanese_product_identity","audit_date":"2026-08-23","notes":"Arclight identifies the 2020 Japanese release as a remake of Studio GG 2017 with 16 additional building tiles and 2 additional maps; 2-4 players; 30 minutes; age 8+","excludes":["unpublished fan variants","community summaries","digital adaptations"]}'::jsonb
  ),
  (
    'designer:studiogg:little-town:2017-official',
    'https://studiogg.doorblog.jp/archives/cat_1309479.html',
    'Studio GG official Little Town Builders archive',
    'designer_official_page',
    'Studio GG',
    'physical',
    'ja',
    '2017-original',
    '{"authority":"designer","role":"lineage_and_core_rule_crosscheck","audit_date":"2026-08-23","notes":"Studio GG describes the design as a 2-4 player resource/building game played over four rounds"}'::jsonb
  ),
  (
    'publisher:iello:little-town:2019-rulebook',
    'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf',
    'IELLO Little Town official rulebook ©2019',
    'publisher_rulebook',
    'IELLO',
    'physical',
    'en',
    '2019-international-remake',
    '{"authority":"publisher","role":"shared_core_rules","audit_date":"2026-08-23","notes":"Used only for core mechanics shared with the Arclight remake; edition-specific building/objective contents are not promoted into Japanese product identity"}'::jsonb
  )
ON CONFLICT (source_id) DO UPDATE SET
  url = EXCLUDED.url,
  document_identity = EXCLUDED.document_identity,
  source_type = EXCLUDED.source_type,
  publisher_name = EXCLUDED.publisher_name,
  platform = EXCLUDED.platform,
  language_code = EXCLUDED.language_code,
  revision_label = EXCLUDED.revision_label,
  trust_metadata = EXCLUDED.trust_metadata,
  updated_at = now();

INSERT INTO public.source_locators (
  locator_id, source_id, page_number, section_heading, external_reference
)
VALUES
  ('little-town:product:jp-identity', 'publisher:arclight:little-town:2020-product', NULL, 'リトルタウンビルダーズ', 'Arclight Japanese remake; released 2020-01-23; 2-4 players; 30 minutes; age 8+; adds 16 building tiles and 2 maps to the Studio GG design'),
  ('little-town:designer:four-rounds', 'designer:studiogg:little-town:2017-official', NULL, 'リトルタウンビルダーズ', 'Studio GG first-party archive describes collecting resources/building and competing for the most VP through four rounds'),
  ('little-town:rulebook:setup', 'publisher:iello:little-town:2019-rulebook', 4, 'GAME SETUP', 'Choose board side; prepare Wheat Fields and market buildings; deal objectives by player count; prepare worker/house pieces; each player gets 3 coins; choose first player'),
  ('little-town:rulebook:round', 'publisher:iello:little-town:2019-rulebook', 5, 'GAMEPLAY / STRUCTURE OF A ROUND', 'Game lasts 4 rounds; each turn choose Gather and Activate or Build a Building; a round ends after all workers are placed'),
  ('little-town:rulebook:gather', 'publisher:iello:little-town:2019-rulebook', 5, 'GATHER AND ACTIVATE', 'Place an unused worker on empty grass; gather from and activate buildings in the 8 surrounding spaces including diagonals; opponent buildings cost 1 coin to activate'),
  ('little-town:rulebook:build', 'publisher:iello:little-town:2019-rulebook', 6, 'BUILD A BUILDING', 'Place worker at Construction Site; choose market building; pay cost; place it on empty grass; mark ownership with house; gain printed construction VP'),
  ('little-town:rulebook:additional', 'publisher:iello:little-town:2019-rulebook', 7, 'ADDITIONAL ACTIONS', 'Objectives may be completed when conditions are met; 3 coins can substitute for one resource when immediately spent'),
  ('little-town:rulebook:round-end', 'publisher:iello:little-town:2019-rulebook', 7, 'END OF THE ROUND', 'Resolve special end-round buildings; feed each worker with Fish/Wheat; lose 3 VP for each unfed worker'),
  ('little-town:rulebook:next-round', 'publisher:iello:little-town:2019-rulebook', 8, 'PREPARE FOR THE NEXT ROUND', 'Retrieve workers, advance round token, pass first-player token; fourth round is the last round'),
  ('little-town:rulebook:end', 'publisher:iello:little-town:2019-rulebook', 8, 'END OF THE GAME', 'Add end-game building VP and 1 VP per set of 3 coins; highest VP wins; tied players share victory')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
  page_number = EXCLUDED.page_number,
  section_heading = EXCLUDED.section_heading,
  external_reference = EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_work_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT g.id, g.work_id INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'little-town'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Little Town Game/Work row is required before applying RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://arclightgames.jp/product/%E3%83%AA%E3%83%88%E3%83%AB%E3%82%BF%E3%82%A6%E3%83%B3%E3%83%93%E3%83%AB%E3%83%80%E3%83%BC%E3%82%BA/',
    source_url = 'https://arclightgames.jp/product/%E3%83%AA%E3%83%88%E3%83%AB%E3%82%BF%E3%82%A6%E3%83%B3%E3%83%93%E3%83%AB%E3%83%80%E3%83%BC%E3%82%BA/',
    source_trust = 'official_publisher',
    edition_label = 'アークライト日本語リメイク版 (2020)',
    language_code = 'ja',
    publisher = 'Arclight / Studio GG',
    published_year = 2020,
    min_players = 2,
    max_players = 4,
    play_time = 30,
    min_age = 8,
    source_revision = 'Arclight 2020 Japanese remake identity + Studio GG lineage + IELLO 2019 official shared-core rulebook',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'アークライト日本語リメイク版 (2020)'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2020-arclight-remake'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'アークライト日本語リメイク版 (2020)',
      'Arclight 2020 Japanese remake identity + Studio GG lineage + IELLO 2019 official shared-core rulebook',
      true, '2020-arclight-remake', 'physical', 'Arclight / Studio GG',
      'active', 'source_bound',
      ARRAY[
        'publisher:arclight:little-town:2020-product',
        'designer:studiogg:little-town:2017-official',
        'publisher:iello:little-town:2019-rulebook'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Arclight 2020 Japanese remake identity + Studio GG lineage + IELLO 2019 official shared-core rulebook',
      is_active = true,
      publisher_name = 'Arclight / Studio GG',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:arclight:little-town:2020-product',
        'designer:studiogg:little-town:2017-official',
        'publisher:iello:little-town:2019-rulebook'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'setup.shared-core', 'setup', 'ゲームボードの使用面を決め、畑と今回使用する建物を市場に準備し、人数に応じて各プレイヤーへ目標カード・ワーカー・家コマを用意する。各プレイヤーは3金を受け取り、スタートプレイヤーを決める。', 0, 'source_bound', 'little-town:rule:setup.shared-core', 'little-town:binding:setup.shared-core', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:setup', '{"scope":"shared_core_only"}'::jsonb),
    (v_ruleset_id, 'game.four-rounds', 'game_end', 'ゲームは全4ラウンドで行い、第4ラウンド終了後に最終得点計算へ進む。', 0, 'source_bound', 'little-town:rule:game.four-rounds', 'little-town:binding:game.four-rounds', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:round', '{"crosscheck":"Studio GG first-party four-round description"}'::jsonb),
    (v_ruleset_id, 'turn.choose-action', 'turn', '自分の手番では未使用のワーカー1個を使い、「資源を得て建物を起動する」か「建物を建設する」のどちらか一方を行う。全員がすべてのワーカーを配置するとそのラウンドが終了する。', 0, 'source_bound', 'little-town:rule:turn.choose-action', 'little-town:binding:turn.choose-action', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:round', '{}'::jsonb),
    (v_ruleset_id, 'action.gather-and-activate', 'action', '資源獲得では未使用のワーカーを空いている草原マスに置き、そのワーカーの周囲8マス（斜めを含む）にある地形から資源を得て、隣接する建物を任意の順で起動できる。各建物はそのワーカーによる1回の配置につき1回だけ起動できる。', 0, 'source_bound', 'little-town:rule:action.gather-and-activate', 'little-town:binding:action.gather-and-activate', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:gather', '{}'::jsonb),
    (v_ruleset_id, 'action.opponent-building-cost', 'condition', '他プレイヤーが所有する建物を起動するときは、その効果を適用する前に所有者へ1金を支払う。自分の建物を起動する場合はこの支払いは不要。', 0, 'source_bound', 'little-town:rule:action.opponent-building-cost', 'little-town:binding:action.opponent-building-cost', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:gather', '{}'::jsonb),
    (v_ruleset_id, 'action.build-building', 'action', '建設では未使用のワーカー1個を建設現場へ置き、市場から建物1枚を選び、記載された資源や金を支払う。その建物を空いている草原マスへ置き、自分の家コマで所有を示し、建設時に記載された勝利点を得る。', 1, 'source_bound', 'little-town:rule:action.build-building', 'little-town:binding:action.build-building', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:build', '{}'::jsonb),
    (v_ruleset_id, 'action.objective-and-substitute', 'action', '目標カードの条件を満たした場合はゲーム中に達成を宣言して対応する勝利点を得られる。また、資源を支払う必要があるときは3金をただちに支払うことで任意の資源1個の代わりにできる。', 2, 'source_bound', 'little-town:rule:action.objective-and-substitute', 'little-town:binding:action.objective-and-substitute', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:additional', '{}'::jsonb),
    (v_ruleset_id, 'round-end.feed-workers', 'round_end', 'ラウンド終了時は、まずラウンド終了時にのみ働く建物の効果を処理し、その後各プレイヤーは自分のワーカー1個につき魚または小麦を1個支払う。食料を支払えないワーカー1個ごとに勝利点を3点失う。', 0, 'source_bound', 'little-town:rule:round-end.feed-workers', 'little-town:binding:round-end.feed-workers', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:round-end', '{}'::jsonb),
    (v_ruleset_id, 'round-end.prepare-next', 'round_end', '第4ラウンド以外のラウンド終了後は各自のワーカーを手元へ戻し、ラウンドマーカーを1つ進め、スタートプレイヤーマーカーを次のプレイヤーへ渡して次ラウンドを始める。', 1, 'source_bound', 'little-town:rule:round-end.prepare-next', 'little-town:binding:round-end.prepare-next', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:next-round', '{}'::jsonb),
    (v_ruleset_id, 'victory.final-scoring', 'victory', '第4ラウンド終了後、ゲーム終了時に得点する建物の勝利点を加え、手元の3金ごとに1勝利点を加える。最も勝利点が多いプレイヤーが勝者となり、最高得点が同点ならそのプレイヤー全員が勝利を共有する。', 0, 'source_bound', 'little-town:rule:victory.final-scoring', 'little-town:binding:victory.final-scoring', 'https://iellogames.com/wp-content/uploads/2019/05/LITTLE-TOWN-Rulebook-EN-light.pdf', 'little-town:rulebook:end', '{}'::jsonb)
  ON CONFLICT (rule_set_id, rule_id) DO UPDATE SET
    node_type = EXCLUDED.node_type,
    normalized_statement = EXCLUDED.normalized_statement,
    sequence = EXCLUDED.sequence,
    verification_status = EXCLUDED.verification_status,
    source_claim_ref = EXCLUDED.source_claim_ref,
    evidence_ref = EXCLUDED.evidence_ref,
    source_url = EXCLUDED.source_url,
    source_locator = EXCLUDED.source_locator,
    metadata = EXCLUDED.metadata,
    updated_at = now();

  INSERT INTO public.claims (
    claim_id, rule_set_id, claim_type, normalized_payload, target_type,
    rule_id, lifecycle_status, generator_provenance
  )
  SELECT
    'little-town:rule:' || rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_source_normalization","audit_date":"2026-08-23","scope":"shared_core_only"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id IN (
      'setup.shared-core','game.four-rounds','turn.choose-action','action.gather-and-activate',
      'action.opponent-building-cost','action.build-building','action.objective-and-substitute',
      'round-end.feed-workers','round-end.prepare-next','victory.final-scoring'
    )
  ON CONFLICT (claim_id) DO UPDATE SET
    rule_set_id = EXCLUDED.rule_set_id,
    claim_type = EXCLUDED.claim_type,
    normalized_payload = EXCLUDED.normalized_payload,
    target_type = EXCLUDED.target_type,
    rule_id = EXCLUDED.rule_id,
    lifecycle_status = EXCLUDED.lifecycle_status,
    generator_provenance = EXCLUDED.generator_provenance,
    updated_at = now();

  INSERT INTO public.evidence_bindings (
    binding_id, claim_id, source_id, locator_id, relation,
    reviewer_provenance, generator_provenance, verified_at
  ) VALUES
    ('little-town:binding:setup.shared-core','little-town:rule:setup.shared-core','publisher:iello:little-town:2019-rulebook','little-town:rulebook:setup','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:game.four-rounds','little-town:rule:game.four-rounds','publisher:iello:little-town:2019-rulebook','little-town:rulebook:round','supports','{"review":"publisher_source","crosscheck":"designer_first_party"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:turn.choose-action','little-town:rule:turn.choose-action','publisher:iello:little-town:2019-rulebook','little-town:rulebook:round','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:action.gather-and-activate','little-town:rule:action.gather-and-activate','publisher:iello:little-town:2019-rulebook','little-town:rulebook:gather','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:action.opponent-building-cost','little-town:rule:action.opponent-building-cost','publisher:iello:little-town:2019-rulebook','little-town:rulebook:gather','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:action.build-building','little-town:rule:action.build-building','publisher:iello:little-town:2019-rulebook','little-town:rulebook:build','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:action.objective-and-substitute','little-town:rule:action.objective-and-substitute','publisher:iello:little-town:2019-rulebook','little-town:rulebook:additional','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:round-end.feed-workers','little-town:rule:round-end.feed-workers','publisher:iello:little-town:2019-rulebook','little-town:rulebook:round-end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:round-end.prepare-next','little-town:rule:round-end.prepare-next','publisher:iello:little-town:2019-rulebook','little-town:rulebook:next-round','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('little-town:binding:victory.final-scoring','little-town:rule:victory.final-scoring','publisher:iello:little-town:2019-rulebook','little-town:rulebook:end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    generator_provenance = EXCLUDED.generator_provenance,
    verified_at = EXCLUDED.verified_at;
END $$;

COMMIT;