BEGIN;

-- Power Grid / 電力会社 Recharged physical rules.
-- The Japanese product identity is bound to Arclight's 2019 localized Recharged edition.
-- Rule substance is normalized from 2F-Spiele's official Recharged base rulebook.
-- Classic 2004, Deluxe, card game, Outpost, expansions, promos and map-specific
-- expansion rules are not folded into this base RuleSet.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:arclight:power-grid-recharged:product',
    'https://arclightgames.jp/product/%E9%9B%BB%E5%8A%9B%E4%BC%9A%E7%A4%BE%E5%85%85%E9%9B%BB%E5%AE%8C%E4%BA%86%EF%BC%81/',
    'Arclight 電力会社 充電完了！ 完全日本語版 official product page',
    'publisher_product_page',
    'Arclight Games',
    'physical',
    'ja',
    '2019-07-18',
    '{"authority":"publisher","role":"canonical_japanese_recharged_product_identity","audit_date":"2026-08-23","excludes":["Power Grid classic 2004","Power Grid Deluxe","Power Grid: The Card Game","Power Grid: Outpost","expansions","promos"]}'::jsonb
  ),
  (
    'publisher:2f:power-grid-recharged:product',
    'https://2f-games.com/2f-spiele/power-grid-game-family/power-grid-recharged-version/',
    '2F-Spiele Power Grid Recharged Version official product page',
    'publisher_product_page',
    '2F-Spiele',
    'physical',
    'de',
    '2019-recharged',
    '{"authority":"publisher","role":"canonical_recharged_edition_identity","audit_date":"2026-08-23"}'::jsonb
  ),
  (
    'publisher:2f:power-grid-recharged:rulebook',
    'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf',
    '2F-Spiele Funkenschlag / Power Grid Recharged official rulebook',
    'publisher_rulebook',
    '2F-Spiele',
    'physical',
    'de',
    '2019-recharged',
    '{"authority":"publisher","role":"canonical_base_rules","audit_date":"2026-08-23"}'::jsonb
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
  ('power-grid-recharged:product:jp-identity', 'publisher:arclight:power-grid-recharged:product', NULL, '電力会社 充電完了！ 完全日本語版', 'Power Grid Recharged Edition; 2-6 players; 120 minutes; released 2019-07-18'),
  ('power-grid-recharged:rulebook:round', 'publisher:2f:power-grid-recharged:rulebook', 3, 'Spielablauf', 'Each round has five phases: determine order, auction plants, buy resources, build houses, bureaucracy'),
  ('power-grid-recharged:rulebook:auction', 'publisher:2f:power-grid-recharged:rulebook', 3, 'Phase 2: Kraftwerke versteigern', 'Each player may buy at most one plant per round; Recharged discount marker lowers the smallest current plant minimum bid to 1 Elektro'),
  ('power-grid-recharged:rulebook:resources', 'publisher:2f:power-grid-recharged:rulebook', 4, 'Phase 3: Rohstoffe kaufen', 'Resources are bought in reverse player order from the cheapest available market spaces, within plant storage limits'),
  ('power-grid-recharged:rulebook:build', 'publisher:2f:power-grid-recharged:rulebook', 4, 'Phase 4: Häuser bauen', 'Build in reverse player order; first city connection costs 10 Elektro plus network connection costs'),
  ('power-grid-recharged:rulebook:bureaucracy', 'publisher:2f:power-grid-recharged:rulebook', 5, 'Phase 5: Bürokratie', 'Operate selected plants, earn money for powered cities, replenish resources, then update the plant market'),
  ('power-grid-recharged:rulebook:steps', 'publisher:2f:power-grid-recharged:rulebook', 7, 'Die 3 Stufen des Spiels', 'Step 2 and Step 3 change city occupancy, connection costs and plant market behavior'),
  ('power-grid-recharged:rulebook:end', 'publisher:2f:power-grid-recharged:rulebook', 8, 'Spielende und Siegbedingung', 'End threshold depends on player count; winner powers the most cities, with remaining money as tie-break')
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
  WHERE g.slug = 'power-grid'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Power Grid Game/Work row is required before applying RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://arclightgames.jp/product/%E9%9B%BB%E5%8A%9B%E4%BC%9A%E7%A4%BE%E5%85%85%E9%9B%BB%E5%AE%8C%E4%BA%86%EF%BC%81/',
    source_url = 'https://arclightgames.jp/product/%E9%9B%BB%E5%8A%9B%E4%BC%9A%E7%A4%BE%E5%85%85%E9%9B%BB%E5%AE%8C%E4%BA%86%EF%BC%81/',
    source_trust = 'official_publisher',
    edition_label = '電力会社 充電完了！ 完全日本語版 (2019 Recharged)',
    language_code = 'ja',
    publisher = '2F-Spiele / Arclight Games',
    source_revision = 'Power Grid Recharged official rulebook; Arclight Japanese edition released 2019-07-18',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = '電力会社 充電完了！ 完全日本語版 (2019 Recharged)'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2019-recharged'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      publication_date, status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', '電力会社 充電完了！ 完全日本語版 (2019 Recharged)',
      '2F-Spiele official Recharged base rulebook + Arclight Japanese product identity',
      true, '2019-recharged', 'physical', '2F-Spiele / Arclight Games',
      DATE '2019-07-18', 'active', 'source_bound',
      ARRAY[
        'publisher:arclight:power-grid-recharged:product',
        'publisher:2f:power-grid-recharged:product',
        'publisher:2f:power-grid-recharged:rulebook'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = '2F-Spiele official Recharged base rulebook + Arclight Japanese product identity',
      is_active = true,
      publisher_name = '2F-Spiele / Arclight Games',
      publication_date = DATE '2019-07-18',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:arclight:power-grid-recharged:product',
        'publisher:2f:power-grid-recharged:product',
        'publisher:2f:power-grid-recharged:rulebook'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'round.five-phases', 'phase', '各ラウンドは、手番順の決定、発電所のオークション、資源購入、都市への建設、官僚フェイズの5段階をこの順に行う。', 0, 'source_bound', 'power-grid-recharged:rule:round.five-phases', 'power-grid-recharged:binding:round.five-phases', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:round', '{}'::jsonb),
    (v_ruleset_id, 'order.ranking', 'phase', '手番順は接続している都市数が多いプレイヤーほど先になる。同数なら、所有する最も番号の大きい発電所を持つプレイヤーを上位とする。', 1, 'source_bound', 'power-grid-recharged:rule:order.ranking', 'power-grid-recharged:binding:order.ranking', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:round', '{}'::jsonb),
    (v_ruleset_id, 'auction.one-plant-and-discount', 'action', '発電所オークションでは各プレイヤーが1ラウンドに購入できる発電所は最大1基。充電完了版ではフェイズ開始時に現在市場の最小発電所へ割引マーカーを置き、その発電所の最低入札額を1エレクトロにする。', 0, 'source_bound', 'power-grid-recharged:rule:auction.one-plant-and-discount', 'power-grid-recharged:binding:auction.one-plant-and-discount', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:auction', '{}'::jsonb),
    (v_ruleset_id, 'resources.reverse-order', 'action', '資源購入は手番順の逆順で行う。各プレイヤーは自分の発電所で保管可能な資源だけを、市場で安い区画から購入する。', 0, 'source_bound', 'power-grid-recharged:rule:resources.reverse-order', 'power-grid-recharged:binding:resources.reverse-order', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:resources', '{}'::jsonb),
    (v_ruleset_id, 'build.network-cost', 'action', '都市への建設も手番順の逆順で行う。最初の都市は空いている都市を選び10エレクトロで接続し、以後の都市では自分の既存ネットワークからの最小接続コストと都市の接続コストを合計して支払う。', 0, 'source_bound', 'power-grid-recharged:rule:build.network-cost', 'power-grid-recharged:binding:build.network-cost', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:build', '{}'::jsonb),
    (v_ruleset_id, 'bureaucracy.power-income', 'action', '官僚フェイズでは運転する発電所を選び、必要な資源を消費して都市へ電力を供給する。収入は実際に電力を供給した都市数で決まり、その後に資源市場を補充し発電所市場を更新する。', 0, 'source_bound', 'power-grid-recharged:rule:bureaucracy.power-income', 'power-grid-recharged:binding:bureaucracy.power-income', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:bureaucracy', '{}'::jsonb),
    (v_ruleset_id, 'step2.city-capacity', 'phase', 'ステップ2では都市の2番目の接続枠が利用可能になり、その接続コストは15エレクトロ。2〜5人戦では誰かが7都市、6人戦では誰かが6都市へ接続したラウンドの官僚フェイズ開始時にステップ2へ移る。', 0, 'source_bound', 'power-grid-recharged:rule:step2.city-capacity', 'power-grid-recharged:binding:step2.city-capacity', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:steps', '{}'::jsonb),
    (v_ruleset_id, 'step3.market-and-city', 'phase', 'ステップ3カードが発電所山札から引かれると所定の次フェイズからステップ3へ移り、発電所市場は6基すべてが現在市場となる。都市の3番目の接続枠も利用可能になり、その接続コストは20エレクトロ。', 1, 'source_bound', 'power-grid-recharged:rule:step3.market-and-city', 'power-grid-recharged:binding:step3.market-and-city', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:steps', '{}'::jsonb),
    (v_ruleset_id, 'game-end.threshold', 'game_end', '建設フェイズ終了後、誰かが人数別の終了都市数以上へ接続していればゲーム終了となる。終了都市数は2人戦18、3〜4人戦17、5人戦15、6人戦14。', 0, 'source_bound', 'power-grid-recharged:rule:game-end.threshold', 'power-grid-recharged:binding:game-end.threshold', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:end', '{}'::jsonb),
    (v_ruleset_id, 'victory.powered-cities', 'victory', 'ゲーム終了時、所有する発電所で最も多くの自分の都市へ電力を供給できるプレイヤーが勝つ。同数なら残金が最も多いプレイヤーが勝つ。', 0, 'source_bound', 'power-grid-recharged:rule:victory.powered-cities', 'power-grid-recharged:binding:victory.powered-cities', 'https://2f-spiele.de/pdf/funkenschlag-recharged-anleitung_de.pdf', 'power-grid-recharged:rulebook:end', '{}'::jsonb)
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
    'power-grid-recharged:rule:' || rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_source_normalization","audit_date":"2026-08-23"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id IN (
      'round.five-phases','order.ranking','auction.one-plant-and-discount',
      'resources.reverse-order','build.network-cost','bureaucracy.power-income',
      'step2.city-capacity','step3.market-and-city','game-end.threshold','victory.powered-cities'
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
    ('power-grid-recharged:binding:round.five-phases','power-grid-recharged:rule:round.five-phases','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:round','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:order.ranking','power-grid-recharged:rule:order.ranking','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:round','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:auction.one-plant-and-discount','power-grid-recharged:rule:auction.one-plant-and-discount','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:auction','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:resources.reverse-order','power-grid-recharged:rule:resources.reverse-order','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:resources','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:build.network-cost','power-grid-recharged:rule:build.network-cost','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:build','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:bureaucracy.power-income','power-grid-recharged:rule:bureaucracy.power-income','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:bureaucracy','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:step2.city-capacity','power-grid-recharged:rule:step2.city-capacity','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:steps','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:step3.market-and-city','power-grid-recharged:rule:step3.market-and-city','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:steps','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:game-end.threshold','power-grid-recharged:rule:game-end.threshold','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('power-grid-recharged:binding:victory.powered-cities','power-grid-recharged:rule:victory.powered-cities','publisher:2f:power-grid-recharged:rulebook','power-grid-recharged:rulebook:end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now())
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
