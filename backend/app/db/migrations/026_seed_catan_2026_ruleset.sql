BEGIN;

-- CATAN Japanese renewed physical base game, 2026 GP Games edition.
-- Official identity is bound to GP Games; base mechanics are normalized from
-- the current CATAN GmbH 6th-edition base-game rulebook and current base FAQ.
-- Pre-2025 international editions, pre-2026 Japanese editions, 5-6 player
-- rules, tournament overrides, variants, and expansions are excluded.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:gp:catan:2026-standard-product',
    'https://www.gp-inc.jp/boardgame_catan_new_s.html',
    'GP Games CATAN Standard Edition 2026 renewed Japanese product page',
    'publisher_product_page',
    'GP Games / CATAN GmbH',
    'physical',
    'ja',
    '2026-renewed',
    '{"authority":"publisher_localization","role":"canonical_japanese_2026_product_identity","audit_date":"2026-08-22","jan":"4543471004512","excludes":["pre-2026 Japanese editions","5-6 player extension","expansions","tournament overrides"]}'::jsonb
  ),
  (
    'publisher:catan:catan:6e-rulebook',
    'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf',
    'CATAN - The Game Rulebook, current 6th edition',
    'publisher_rulebook',
    'CATAN GmbH / CATAN Studio',
    'physical',
    'en',
    '6th-edition-2025',
    '{"authority":"publisher","role":"canonical_base_rules_for_current_6th_edition","audit_date":"2026-08-22","linked_from":"https://www.catan.com/catan"}'::jsonb
  ),
  (
    'publisher:catan:catan:basegame-faq',
    'https://www.catan.com/faq/basegame',
    'CATAN official Basegame FAQ',
    'publisher_faq',
    'CATAN GmbH / CATAN Studio',
    'physical',
    'en',
    'current',
    '{"authority":"publisher","role":"clarification_only","audit_date":"2026-08-22"}'::jsonb
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
  locator_id, source_id, section_heading, external_reference
)
VALUES
  ('catan:gp:identity', 'publisher:gp:catan:2026-standard-product', 'カタン スタンダード版', '2026 renewed Japanese standard edition; JAN 4543471004512; 3-4 players; age 8+; about 60 minutes'),
  ('catan:6e:setup', 'publisher:catan:catan:6e-rulebook', 'SET-UP', 'initial settlements and roads; starting resources from second settlement'),
  ('catan:6e:production', 'publisher:catan:catan:6e-rulebook', 'PRODUCTION PHASE', 'roll two dice; settlements produce one and cities two resources when adjacent number produces'),
  ('catan:6e:robber', 'publisher:catan:catan:6e-rulebook', 'ROLLING A 7 AND ACTIVATING THE ROBBER', 'no production; players above seven resource cards discard half rounded down; move robber and steal one random adjacent resource'),
  ('catan:faq:robber', 'publisher:catan:catan:basegame-faq', 'Seven and Robber', 'current official clarifications for seven/robber resolution and blocked production'),
  ('catan:6e:trade', 'publisher:catan:catan:6e-rulebook', 'TRADE', 'trade with players and supply; maritime trade and harbors'),
  ('catan:6e:build', 'publisher:catan:catan:6e-rulebook', 'BUILDING COSTS', 'road, settlement, city, and development-card resource costs'),
  ('catan:6e:development', 'publisher:catan:catan:6e-rulebook', 'DEVELOPMENT CARDS', 'development card purchase/play restrictions and card categories'),
  ('catan:6e:victory', 'publisher:catan:catan:6e-rulebook', 'END OF THE GAME', '10 or more victory points during your turn ends the game'),
  ('catan:faq:development', 'publisher:catan:catan:basegame-faq', 'Development Cards in General', 'one development card per turn; normally not on the turn bought')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
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
  WHERE g.slug = 'catan'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Catan Game/Work row is required before applying the 2026 RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://www.gp-inc.jp/boardgame_catan_new_s.html',
    source_url = 'https://www.gp-inc.jp/boardgame_catan_new_s.html',
    source_trust = 'official_publisher',
    edition_label = 'GP Games 日本語版 スタンダード版 (2026リニューアル)',
    language_code = 'ja',
    publisher = 'CATAN GmbH / GP Games',
    source_revision = 'GP Games 2026 renewed Japanese product / CATAN current 6th-edition base rules',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'GP Games 日本語版 スタンダード版 (2026リニューアル)'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2026-renewed-6e'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'GP Games 日本語版 スタンダード版 (2026リニューアル)',
      'GP Games 2026 renewed Japanese product + CATAN current 6th-edition base rules',
      true, '2026-renewed-6e', 'physical', 'CATAN GmbH / GP Games',
      'active', 'source_bound',
      ARRAY[
        'publisher:gp:catan:2026-standard-product',
        'publisher:catan:catan:6e-rulebook',
        'publisher:catan:catan:basegame-faq'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'GP Games 2026 renewed Japanese product + CATAN current 6th-edition base rules',
      is_active = true,
      publisher_name = 'CATAN GmbH / GP Games',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:gp:catan:2026-standard-product',
        'publisher:catan:catan:6e-rulebook',
        'publisher:catan:catan:basegame-faq'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'setup.initial-placement', 'setup', '各プレイヤーはゲーム開始時に開拓地2個と、それぞれに接続する街道2本を配置する。2個目の開拓地に隣接する地形から初期資源を受け取る。', 0, 'source_bound', 'catan:2026:rule:setup.initial-placement', 'catan:2026:binding:setup.initial-placement', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:setup', '{}'::jsonb),
    (v_ruleset_id, 'turn.production', 'turn', '手番の生産フェイズで2個のダイスを振る。出目に対応する地形に隣接する自分の開拓地1個につき資源1枚、都市1個につき資源2枚を受け取る。', 0, 'source_bound', 'catan:2026:rule:turn.production', 'catan:2026:binding:turn.production', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:production', '{}'::jsonb),
    (v_ruleset_id, 'turn.seven-robber', 'turn', '出目が7なら資源は産出しない。資源カードを8枚以上持つ各プレイヤーはその半数を端数切り捨てでサプライへ戻し、手番プレイヤーは盗賊を別の地形へ移動して、その地形に隣接する相手1人から資源カード1枚を無作為に奪う。盗賊のいる地形は資源を産出しない。', 1, 'source_bound', 'catan:2026:rule:turn.seven-robber', 'catan:2026:binding:turn.seven-robber', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:robber', '{}'::jsonb),
    (v_ruleset_id, 'action.trade', 'action', '生産または7の処理後、手番プレイヤーは他プレイヤーと資源を交換でき、サプライとの海上交易も行える。港を利用できる場合は対応する有利な交換比率を使える。', 0, 'source_bound', 'catan:2026:rule:action.trade', 'catan:2026:binding:action.trade', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:trade', '{}'::jsonb),
    (v_ruleset_id, 'build.road', 'action', '街道1本の建設コストは木材1枚とレンガ1枚。新しい街道は自分の既存の街道・開拓地・都市につながるように配置する。', 1, 'source_bound', 'catan:2026:rule:build.road', 'catan:2026:binding:build.road', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:build', '{}'::jsonb),
    (v_ruleset_id, 'build.settlement', 'action', '開拓地1個の建設コストは木材1枚、レンガ1枚、羊毛1枚、穀物1枚。自分の街道に接続し、隣接する3交差点に他の開拓地・都市がない交差点にのみ建設でき、1勝利ポイントになる。', 2, 'source_bound', 'catan:2026:rule:build.settlement', 'catan:2026:binding:build.settlement', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:build', '{}'::jsonb),
    (v_ruleset_id, 'build.city', 'action', '都市への発展コストは穀物2枚と鉱石3枚。自分の開拓地を置き換えて建設し、2勝利ポイントになり、隣接する地形から開拓地の2倍の資源を産出する。', 3, 'source_bound', 'catan:2026:rule:build.city', 'catan:2026:binding:build.city', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:build', '{}'::jsonb),
    (v_ruleset_id, 'build.development-card', 'action', '発展カード1枚の購入コストは羊毛1枚、穀物1枚、鉱石1枚。購入したカードは原則としてその手番には使用できず、使用する発展カードは1手番に1枚まで。', 4, 'source_bound', 'catan:2026:rule:build.development-card', 'catan:2026:binding:build.development-card', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:development', '{}'::jsonb),
    (v_ruleset_id, 'victory.longest-road', 'scoring', '最長交易路の条件を満たして保持しているプレイヤーは2勝利ポイントを得る。', 0, 'source_bound', 'catan:2026:rule:victory.longest-road', 'catan:2026:binding:victory.longest-road', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:victory', '{}'::jsonb),
    (v_ruleset_id, 'victory.largest-army', 'scoring', '最大騎士力の条件を満たして保持しているプレイヤーは2勝利ポイントを得る。', 1, 'source_bound', 'catan:2026:rule:victory.largest-army', 'catan:2026:binding:victory.largest-army', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:victory', '{}'::jsonb),
    (v_ruleset_id, 'game-end.ten-vp', 'game_end', '自分の手番中に勝利ポイントが10点以上になった時点でゲームは終了し、そのプレイヤーが勝者となる。', 0, 'source_bound', 'catan:2026:rule:game-end.ten-vp', 'catan:2026:binding:game-end.ten-vp', 'https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN%E2%80%93The%20Game%20Rulebook%20secure%20%281%29.pdf', 'catan:6e:victory', '{}'::jsonb)
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
    'catan:2026:rule:' || rn.rule_id,
    v_ruleset_id,
    'rule_statement',
    jsonb_build_object('statement', rn.normalized_statement, 'source_scope', 'CATAN current 6th-edition base physical rules; GP Games Japanese 2026 renewed identity'),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"seed":"026_seed_catan_2026_ruleset","audit_date":"2026-08-22","method":"manual_primary_source_normalization"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'catan:2026:%'
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
  )
  SELECT
    'catan:2026:binding:' || rn.rule_id,
    'catan:2026:rule:' || rn.rule_id,
    'publisher:catan:catan:6e-rulebook',
    rn.source_locator,
    'supports',
    '{"audit_date":"2026-08-22","method":"manual_primary_source_verification"}'::jsonb,
    '{"seed":"026_seed_catan_2026_ruleset"}'::jsonb,
    now()
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'catan:2026:%'
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
