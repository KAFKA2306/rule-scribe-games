BEGIN;

-- YRO production pilot for Ontology v2.
--
-- Source policy:
--   * BGA Release 260725-1445 live game panel is canonical for this BGA RuleSet.
--   * The BGA community wiki is retained as a lower-authority contradictory
--     source for its stale three-phase description; it never defines this RuleSet.
--   * Studio Supernova is retained as publisher/product provenance only.
--   * No individual Adventurer/Quest records are generated because no complete
--     first-party component list was found during the 2026-08-14 audit.
--
-- This migration is intentionally idempotent and resolves generated database
-- identifiers by canonical natural keys instead of hardcoding production UUIDs.

INSERT INTO public.evidence_sources (
  source_id,
  url,
  document_identity,
  source_type,
  publisher_name,
  platform,
  language_code,
  revision_label,
  trust_metadata
)
VALUES
  (
    'bga:yro:260725-1445',
    'https://en.boardgamearena.com/gamepanel?game=yro',
    'Board Game Arena YRO live game page / Rules summary / Release 260725-1445',
    'platform_rules_summary',
    'Studio Supernova',
    'Board Game Arena',
    'en',
    '260725-1445',
    '{"audit_date":"2026-08-14","authority":"current_platform_implementation","role":"canonical_for_bga_implementation","scope":"rules_and_platform_metadata"}'::jsonb
  ),
  (
    'bga-wiki:yro:2026-08-14',
    'https://en.doc.boardgamearena.com/Gamehelpyro',
    'Board Game Arena community wiki Gamehelpyro snapshot observed 2026-08-14',
    'community_rules_wiki',
    NULL,
    'Board Game Arena',
    'en',
    NULL,
    '{"audit_date":"2026-08-14","authority":"community","role":"noncanonical_conflicting_context","conflict":"three_phase_summary_vs_live_six_phase_release"}'::jsonb
  ),
  (
    'publisher:yro:studio-supernova-product',
    'https://www.studiosupernova.it/products/yro',
    'Studio Supernova YRO product page',
    'publisher_product_page',
    'Studio Supernova',
    NULL,
    'it',
    NULL,
    '{"audit_date":"2026-08-14","authority":"publisher","role":"publisher_product_context","scope":"product_and_component_classes_not_detailed_rules"}'::jsonb
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
  locator_id,
  source_id,
  section_heading,
  external_reference
)
VALUES
  ('yro:bga:overview', 'bga:yro:260725-1445', 'YRO overview', 'game metadata, factions, 3x3 grid and core resources'),
  ('yro:bga:setup', 'bga:yro:260725-1445', 'SETUP', 'player board, markers, shared boards, starting Money/hand and Quest display'),
  ('yro:bga:gameplay', 'bga:yro:260725-1445', 'GAMEPLAY', 'six simultaneous phases per round'),
  ('yro:bga:phase:discard-draw', 'bga:yro:260725-1445', 'Discard & Draw Phase', 'phase 1'),
  ('yro:bga:phase:recruit', 'bga:yro:260725-1445', 'Recruit Phase', 'phase 2'),
  ('yro:bga:phase:combat', 'bga:yro:260725-1445', 'Combat Phase', 'phase 3'),
  ('yro:bga:phase:production', 'bga:yro:260725-1445', 'Production Phase', 'phase 4'),
  ('yro:bga:phase:income', 'bga:yro:260725-1445', 'Income Phase', 'phase 5'),
  ('yro:bga:phase:victory-point', 'bga:yro:260725-1445', 'Victory Point Phase', 'phase 6'),
  ('yro:bga:key-concepts', 'bga:yro:260725-1445', 'KEY CONCEPTS', 'factions, professions, Technology, Magic and Resources'),
  ('yro:bga:end-game', 'bga:yro:260725-1445', 'END OF GAME', '9-card/40-VP trigger, Money conversion and winner'),
  ('yro:bga-wiki:gameplay', 'bga-wiki:yro:2026-08-14', 'GAMEPLAY (Multiple Rounds)', 'community wiki describes three simultaneous phases'),
  ('yro:publisher:description', 'publisher:yro:studio-supernova-product', 'YRO product description', 'adventurers, factions, formation, resources, strength, coins and VP')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
  section_heading = EXCLUDED.section_heading,
  external_reference = EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_work_id uuid;
  v_ruleset_id uuid;
  v_catalog_id uuid;
BEGIN
  SELECT g.id, g.work_id
    INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'yro'
    AND g.identity_status = 'verified'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'YRO canonical verified Game row is required before applying the YRO pilot seed';
  END IF;

  SELECT rs.id
    INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'en'
    AND COALESCE(rs.edition_label, '') = 'BGA Release 260725-1445'
    AND COALESCE(rs.platform, '') = 'Board Game Arena'
    AND COALESCE(rs.revision_label, '') = '260725-1445'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id,
      work_id,
      version,
      schema_version,
      language_code,
      edition_label,
      source_revision,
      is_active,
      revision_label,
      platform,
      publisher_name,
      status,
      verification_status,
      source_ids
    ) VALUES (
      v_game_id,
      v_work_id,
      1,
      '1.0',
      'en',
      'BGA Release 260725-1445',
      'BGA YRO Release 260725-1445; primary-source audit 2026-08-14',
      true,
      '260725-1445',
      'Board Game Arena',
      'Studio Supernova',
      'active',
      'source_bound',
      ARRAY['bga:yro:260725-1445']::text[]
    )
    RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets
    SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'BGA YRO Release 260725-1445; primary-source audit 2026-08-14',
      is_active = true,
      publisher_name = 'Studio Supernova',
      publication_date = NULL,
      effective_date = NULL,
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY['bga:yro:260725-1445']::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.component_catalogs (rule_set_id, schema_version, metadata)
  VALUES (
    v_ruleset_id,
    '1.0',
    '{"coverage_status":"incomplete","enumeration_status":"unknown","source_policy":"first_party_only","audit_date":"2026-08-14","missing_reason":"No complete first-party Adventurer/Quest list was discovered; individual components must not be inferred.","source_ids":["bga:yro:260725-1445","publisher:yro:studio-supernova-product"]}'::jsonb
  )
  ON CONFLICT (rule_set_id) DO UPDATE SET
    schema_version = EXCLUDED.schema_version,
    metadata = EXCLUDED.metadata,
    updated_at = now()
  RETURNING id INTO v_catalog_id;

  INSERT INTO public.component_sets (
    catalog_id,
    rule_set_id,
    component_set_id,
    canonical_name,
    kind,
    verification_status,
    source_ids,
    metadata
  ) VALUES
    (
      v_catalog_id,
      v_ruleset_id,
      'adventurers',
      'Adventurers',
      'card',
      'source_bound',
      ARRAY['bga:yro:260725-1445','publisher:yro:studio-supernova-product']::text[],
      '{"coverage_status":"incomplete","enumeration_status":"not_enumerated"}'::jsonb
    ),
    (
      v_catalog_id,
      v_ruleset_id,
      'quests',
      'Quests',
      'card',
      'source_bound',
      ARRAY['bga:yro:260725-1445']::text[],
      '{"coverage_status":"incomplete","enumeration_status":"not_enumerated"}'::jsonb
    )
  ON CONFLICT (rule_set_id, component_set_id) DO UPDATE SET
    catalog_id = EXCLUDED.catalog_id,
    canonical_name = EXCLUDED.canonical_name,
    kind = EXCLUDED.kind,
    verification_status = EXCLUDED.verification_status,
    source_ids = EXCLUDED.source_ids,
    metadata = EXCLUDED.metadata,
    updated_at = now();

  INSERT INTO public.component_property_definitions (
    catalog_id,
    rule_set_id,
    property_key,
    labels,
    value_type,
    cardinality,
    filterable,
    sortable,
    verification_status,
    source_ids,
    metadata
  ) VALUES
    (v_catalog_id, v_ruleset_id, 'faction', '{"en":"Faction","ja":"派閥"}'::jsonb, 'text', 'one', true, false, 'source_bound', ARRAY['bga:yro:260725-1445','publisher:yro:studio-supernova-product']::text[], '{"applies_to":["adventurers"]}'::jsonb),
    (v_catalog_id, v_ruleset_id, 'profession', '{"en":"Profession","ja":"職業"}'::jsonb, 'text', 'one', true, false, 'source_bound', ARRAY['bga:yro:260725-1445']::text[], '{"applies_to":["adventurers"]}'::jsonb),
    (v_catalog_id, v_ruleset_id, 'combat_value', '{"en":"Combat Value","ja":"戦闘値"}'::jsonb, 'integer', 'one', false, true, 'source_bound', ARRAY['bga:yro:260725-1445']::text[], '{"applies_to":["adventurers"]}'::jsonb),
    (v_catalog_id, v_ruleset_id, 'recruit_cost', '{"en":"Recruit Cost","ja":"雇用コスト"}'::jsonb, 'integer', 'one', false, true, 'source_bound', ARRAY['bga:yro:260725-1445']::text[], '{"applies_to":["adventurers"]}'::jsonb)
  ON CONFLICT (rule_set_id, property_key) DO UPDATE SET
    catalog_id = EXCLUDED.catalog_id,
    labels = EXCLUDED.labels,
    value_type = EXCLUDED.value_type,
    cardinality = EXCLUDED.cardinality,
    filterable = EXCLUDED.filterable,
    sortable = EXCLUDED.sortable,
    verification_status = EXCLUDED.verification_status,
    source_ids = EXCLUDED.source_ids,
    metadata = EXCLUDED.metadata,
    updated_at = now();

  INSERT INTO public.rule_nodes (
    rule_set_id,
    rule_id,
    node_type,
    normalized_statement,
    sequence,
    phase_rule_id,
    verification_status,
    source_claim_ref,
    evidence_ref,
    source_url,
    source_locator,
    metadata
  ) VALUES
    (v_ruleset_id, 'setup.core', 'setup', 'Give each player a board, four track markers, 3 Money and five cards; place the shared Combat/Victory board and face-up Quests.', 0, NULL, 'source_bound', 'yro:bga:260725-1445:rule:setup.core', 'yro:bga:260725-1445:binding:setup.core', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:setup', '{"vrchat_capabilities":{"board":"required","tokens":"required","deck":"required"}}'::jsonb),
    (v_ruleset_id, 'phase.round-structure', 'phase', 'Each round has six phases that players resolve simultaneously.', 0, NULL, 'source_bound', 'yro:bga:260725-1445:rule:phase.round-structure', 'yro:bga:260725-1445:binding:phase.round-structure', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:gameplay', '{}'::jsonb),
    (v_ruleset_id, 'phase.1.discard-draw', 'phase', 'Players simultaneously discard any number of hand cards and draw back to five.', 1, NULL, 'source_bound', 'yro:bga:260725-1445:rule:phase.1.discard-draw', 'yro:bga:260725-1445:binding:phase.1.discard-draw', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:discard-draw', '{"vrchat_capabilities":{"deck":"required"}}'::jsonb),
    (v_ruleset_id, 'phase.2.recruit', 'phase', 'Players simultaneously resolve recruiting after the discard/draw phase.', 2, NULL, 'source_bound', 'yro:bga:260725-1445:rule:phase.2.recruit', 'yro:bga:260725-1445:binding:phase.2.recruit', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:recruit', '{"vrchat_capabilities":{"deck":"required","board":"required"}}'::jsonb),
    (v_ruleset_id, 'phase.3.combat', 'phase', 'Compare Combat Power among all players and award VP according to the ranking for the player count.', 3, NULL, 'source_bound', 'yro:bga:260725-1445:rule:phase.3.combat', 'yro:bga:260725-1445:binding:phase.3.combat', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:combat', '{}'::jsonb),
    (v_ruleset_id, 'phase.4.production', 'phase', 'Resolve Production text on recruited Adventurers that have the Production symbol.', 4, NULL, 'source_bound', 'yro:bga:260725-1445:rule:phase.4.production', 'yro:bga:260725-1445:binding:phase.4.production', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:production', '{}'::jsonb),
    (v_ruleset_id, 'phase.5.income', 'phase', 'Gain 3 Money, then gain additional Money from recruited Adventurers with Income icons.', 5, NULL, 'source_bound', 'yro:bga:260725-1445:rule:phase.5.income', 'yro:bga:260725-1445:binding:phase.5.income', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:income', '{}'::jsonb),
    (v_ruleset_id, 'phase.6.victory-point', 'phase', 'Gain VP shown by recruited Adventurers with VP icons.', 6, NULL, 'source_bound', 'yro:bga:260725-1445:rule:phase.6.victory-point', 'yro:bga:260725-1445:binding:phase.6.victory-point', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:victory-point', '{}'::jsonb),
    (v_ruleset_id, 'action.recruit', 'action', 'Recruit zero, one or two hand cards by paying their cost; each card not played during this choice earns 1 Money.', 0, 'phase.2.recruit', 'source_bound', 'yro:bga:260725-1445:rule:action.recruit', 'yro:bga:260725-1445:binding:action.recruit', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:recruit', '{"vrchat_capabilities":{"deck":"required"}}'::jsonb),
    (v_ruleset_id, 'action.place-adventurer', 'action', 'Place a recruited card in the 3x3 grid orthogonally adjacent to an existing card.', 1, 'phase.2.recruit', 'source_bound', 'yro:bga:260725-1445:rule:action.place-adventurer', 'yro:bga:260725-1445:binding:action.place-adventurer', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:recruit', '{"vrchat_capabilities":{"board":"required"}}'::jsonb),
    (v_ruleset_id, 'effect.combat-vp', 'effect', 'Combat ranking grants VP according to player count, including tie handling described by the BGA implementation.', 0, 'phase.3.combat', 'source_bound', 'yro:bga:260725-1445:rule:effect.combat-vp', 'yro:bga:260725-1445:binding:effect.combat-vp', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:combat', '{}'::jsonb),
    (v_ruleset_id, 'effect.production', 'effect', 'Production effects activate during the Production phase, commonly adding Magic or Technology.', 0, 'phase.4.production', 'source_bound', 'yro:bga:260725-1445:rule:effect.production', 'yro:bga:260725-1445:binding:effect.production', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:production', '{}'::jsonb),
    (v_ruleset_id, 'effect.income', 'effect', 'Income grants the base 3 Money plus additional Money specified by Income icons.', 0, 'phase.5.income', 'source_bound', 'yro:bga:260725-1445:rule:effect.income', 'yro:bga:260725-1445:binding:effect.income', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:income', '{}'::jsonb),
    (v_ruleset_id, 'effect.victory-point', 'effect', 'VP icons on recruited Adventurers add the specified VP during the Victory Point phase.', 0, 'phase.6.victory-point', 'source_bound', 'yro:bga:260725-1445:rule:effect.victory-point', 'yro:bga:260725-1445:binding:effect.victory-point', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:phase:victory-point', '{}'::jsonb),
    (v_ruleset_id, 'game-end.trigger', 'game_end', 'End the game after the round in which a player has nine cards in their grid or reaches 40 VP.', 0, NULL, 'source_bound', 'yro:bga:260725-1445:rule:game-end.trigger', 'yro:bga:260725-1445:binding:game-end.trigger', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:end-game', '{}'::jsonb),
    (v_ruleset_id, 'scoring.money-conversion', 'scoring', 'At game end, each complete set of 3 remaining Money is worth 1 VP.', 0, NULL, 'source_bound', 'yro:bga:260725-1445:rule:scoring.money-conversion', 'yro:bga:260725-1445:binding:scoring.money-conversion', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:end-game', '{}'::jsonb),
    (v_ruleset_id, 'victory.most-vp', 'victory', 'The player with the most VP wins.', 0, NULL, 'source_bound', 'yro:bga:260725-1445:rule:victory.most-vp', 'yro:bga:260725-1445:binding:victory.most-vp', 'https://en.boardgamearena.com/gamepanel?game=yro', 'yro:bga:end-game', '{}'::jsonb)
  ON CONFLICT (rule_set_id, rule_id) DO UPDATE SET
    node_type = EXCLUDED.node_type,
    normalized_statement = EXCLUDED.normalized_statement,
    sequence = EXCLUDED.sequence,
    phase_rule_id = EXCLUDED.phase_rule_id,
    verification_status = EXCLUDED.verification_status,
    source_claim_ref = EXCLUDED.source_claim_ref,
    evidence_ref = EXCLUDED.evidence_ref,
    source_url = EXCLUDED.source_url,
    source_locator = EXCLUDED.source_locator,
    metadata = EXCLUDED.metadata,
    updated_at = now();

  -- Rule edges have no natural unique constraint in schema v1, so insert only
  -- missing canonical relations. This preserves re-run idempotency.
  INSERT INTO public.rule_edges (rule_set_id, from_rule_id, to_rule_id, relation_type, sequence, metadata)
  SELECT v_ruleset_id, e.from_rule_id, e.to_rule_id, e.relation_type, e.sequence, '{"seed_id":"yro-bga-260725-1445"}'::jsonb
  FROM (VALUES
    ('phase.round-structure','phase.1.discard-draw','contains',1),
    ('phase.round-structure','phase.2.recruit','contains',2),
    ('phase.round-structure','phase.3.combat','contains',3),
    ('phase.round-structure','phase.4.production','contains',4),
    ('phase.round-structure','phase.5.income','contains',5),
    ('phase.round-structure','phase.6.victory-point','contains',6),
    ('phase.1.discard-draw','phase.2.recruit','next',1),
    ('phase.2.recruit','phase.3.combat','next',2),
    ('phase.3.combat','phase.4.production','next',3),
    ('phase.4.production','phase.5.income','next',4),
    ('phase.5.income','phase.6.victory-point','next',5),
    ('phase.2.recruit','action.recruit','contains',0),
    ('phase.2.recruit','action.place-adventurer','contains',1),
    ('phase.3.combat','effect.combat-vp','contains',0),
    ('phase.4.production','effect.production','contains',0),
    ('phase.5.income','effect.income','contains',0),
    ('phase.6.victory-point','effect.victory-point','contains',0),
    ('game-end.trigger','scoring.money-conversion','results_in',0),
    ('scoring.money-conversion','victory.most-vp','results_in',0)
  ) AS e(from_rule_id, to_rule_id, relation_type, sequence)
  WHERE NOT EXISTS (
    SELECT 1
    FROM public.rule_edges re
    WHERE re.rule_set_id = v_ruleset_id
      AND re.from_rule_id = e.from_rule_id
      AND re.to_rule_id = e.to_rule_id
      AND re.relation_type = e.relation_type
  );

  INSERT INTO public.claims (
    claim_id,
    rule_set_id,
    claim_type,
    normalized_payload,
    target_type,
    rule_id,
    lifecycle_status,
    generator_provenance
  )
  SELECT
    'yro:bga:260725-1445:rule:' || rn.rule_id,
    v_ruleset_id,
    'rule_statement',
    jsonb_build_object('statement', rn.normalized_statement, 'source_scope', 'BGA live implementation'),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"seed":"017_seed_yro_bga_260725_1445","audit_date":"2026-08-14","method":"primary-source normalization"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'yro:bga:260725-1445:%'
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
    binding_id,
    claim_id,
    source_id,
    locator_id,
    relation,
    reviewer_provenance,
    generator_provenance
  )
  SELECT
    'yro:bga:260725-1445:binding:' || rn.rule_id,
    'yro:bga:260725-1445:rule:' || rn.rule_id,
    'bga:yro:260725-1445',
    rn.source_locator,
    'supports',
    '{"audit_date":"2026-08-14","method":"manual primary-source verification","source_scope":"BGA live implementation"}'::jsonb,
    '{"seed":"017_seed_yro_bga_260725_1445"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'yro:bga:260725-1445:%'
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    generator_provenance = EXCLUDED.generator_provenance;

  -- Preserve the currently visible community-wiki disagreement instead of
  -- deleting or silently normalizing it into the live BGA RuleSet.
  INSERT INTO public.evidence_bindings (
    binding_id,
    claim_id,
    source_id,
    locator_id,
    relation,
    reviewer_provenance,
    generator_provenance
  ) VALUES (
    'yro:bga:260725-1445:binding:phase.round-structure:wiki-conflict',
    'yro:bga:260725-1445:rule:phase.round-structure',
    'bga-wiki:yro:2026-08-14',
    'yro:bga-wiki:gameplay',
    'contradicts',
    '{"audit_date":"2026-08-14","method":"source-conflict preservation","canonical_preference":"live BGA release 260725-1445"}'::jsonb,
    '{"seed":"017_seed_yro_bga_260725_1445"}'::jsonb
  )
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    generator_provenance = EXCLUDED.generator_provenance;

  -- Preserve directly observable platform metadata as separate claims rather
  -- than treating the Game row itself as evidence.
  INSERT INTO public.claims (
    claim_id,
    rule_set_id,
    claim_type,
    normalized_payload,
    target_type,
    field_path,
    lifecycle_status,
    generator_provenance
  ) VALUES
    ('yro:bga:260725-1445:meta:min-players', v_ruleset_id, 'platform_metadata', '{"value":1}'::jsonb, 'game_metadata', 'min_players', 'accepted', '{"seed":"017_seed_yro_bga_260725_1445","audit_date":"2026-08-14"}'::jsonb),
    ('yro:bga:260725-1445:meta:max-players', v_ruleset_id, 'platform_metadata', '{"value":5}'::jsonb, 'game_metadata', 'max_players', 'accepted', '{"seed":"017_seed_yro_bga_260725_1445","audit_date":"2026-08-14"}'::jsonb),
    ('yro:bga:260725-1445:meta:play-time', v_ruleset_id, 'platform_metadata', '{"value":6,"unit":"minutes"}'::jsonb, 'game_metadata', 'play_time', 'accepted', '{"seed":"017_seed_yro_bga_260725_1445","audit_date":"2026-08-14"}'::jsonb)
  ON CONFLICT (claim_id) DO UPDATE SET
    rule_set_id = EXCLUDED.rule_set_id,
    claim_type = EXCLUDED.claim_type,
    normalized_payload = EXCLUDED.normalized_payload,
    target_type = EXCLUDED.target_type,
    field_path = EXCLUDED.field_path,
    lifecycle_status = EXCLUDED.lifecycle_status,
    generator_provenance = EXCLUDED.generator_provenance,
    updated_at = now();

  INSERT INTO public.evidence_bindings (
    binding_id,
    claim_id,
    source_id,
    locator_id,
    relation,
    reviewer_provenance,
    generator_provenance
  ) VALUES
    ('yro:bga:260725-1445:binding:meta:min-players', 'yro:bga:260725-1445:meta:min-players', 'bga:yro:260725-1445', 'yro:bga:overview', 'supports', '{"audit_date":"2026-08-14","method":"manual primary-source verification"}'::jsonb, '{"seed":"017_seed_yro_bga_260725_1445"}'::jsonb),
    ('yro:bga:260725-1445:binding:meta:max-players', 'yro:bga:260725-1445:meta:max-players', 'bga:yro:260725-1445', 'yro:bga:overview', 'supports', '{"audit_date":"2026-08-14","method":"manual primary-source verification"}'::jsonb, '{"seed":"017_seed_yro_bga_260725_1445"}'::jsonb),
    ('yro:bga:260725-1445:binding:meta:play-time', 'yro:bga:260725-1445:meta:play-time', 'bga:yro:260725-1445', 'yro:bga:overview', 'supports', '{"audit_date":"2026-08-14","method":"manual primary-source verification"}'::jsonb, '{"seed":"017_seed_yro_bga_260725_1445"}'::jsonb)
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    generator_provenance = EXCLUDED.generator_provenance;
END $$;

COMMIT;
