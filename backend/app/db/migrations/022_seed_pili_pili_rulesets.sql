BEGIN;

-- Keep ATM Gaming's current physical product and the Board Game Arena
-- implementation as distinct RuleSets. The publisher page currently conflicts
-- with itself on the number of Pili cards (23 in the card overview, 22 in the
-- FAQ), so neither value is promoted to an accepted scalar.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:atm:pili-pili:current',
    'https://atmgaming.com/pilipili-fr',
    'ATM Gaming Pili Pili current French product/rules page',
    'publisher_product_rules_page',
    'ATM Gaming',
    NULL,
    'fr',
    NULL,
    '{"audit_date":"2026-08-22","authority":"publisher","role":"canonical_for_current_physical_product","known_conflict":"pili_card_count_23_overview_vs_22_faq"}'::jsonb
  ),
  (
    'bga:pili-pili:260623-1715',
    'https://ja.boardgamearena.com/gamepanel?game=pilipili',
    'Board Game Arena Pili Pili live game page / Release 260623-1715',
    'authorized_platform_rules_summary',
    'ATM Gaming',
    'Board Game Arena',
    'ja',
    '260623-1715',
    '{"audit_date":"2026-08-22","authority":"authorized_platform_implementation","role":"canonical_for_bga_implementation"}'::jsonb
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
  (
    'pili-pili:publisher:card-overview',
    'publisher:atm:pili-pili:current',
    'Aperçu des cartes',
    '55 numbered cards; 40 Mission cards; 23 PILIS; 1 Joker'
  ),
  (
    'pili-pili:publisher:faq-box',
    'publisher:atm:pili-pili:current',
    'Que contient la boîte du jeu ?',
    '55 numbered cards; 1 Joker; 40 Mission cards; 22 double-sided Pili cards'
  ),
  (
    'pili-pili:bga:rules-summary',
    'bga:pili-pili:260623-1715',
    'ルールの概要',
    'BGA Release 260623-1715 rules summary and component list'
  )
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
  section_heading = EXCLUDED.section_heading,
  external_reference = EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_work_id uuid;
  v_physical_id uuid;
  v_bga_id uuid;
BEGIN
  SELECT g.id, g.work_id
    INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'pili-pili'
    AND g.identity_status = 'verified'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Verified canonical Pili Pili Game row is required before RuleSet seed';
  END IF;

  SELECT rs.id INTO v_physical_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'fr'
    AND COALESCE(rs.edition_label, '') = 'ATM Gaming physical product'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = ''
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_physical_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, platform, publisher_name, status,
      verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'fr', 'ATM Gaming physical product',
      'Current ATM Gaming product/rules page audited 2026-08-22; Pili count remains conflicted',
      true, 'physical', 'ATM Gaming', 'active', 'source_bound',
      ARRAY['publisher:atm:pili-pili:current']::text[]
    ) RETURNING id INTO v_physical_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Current ATM Gaming product/rules page audited 2026-08-22; Pili count remains conflicted',
      is_active = true,
      publisher_name = 'ATM Gaming',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY['publisher:atm:pili-pili:current']::text[],
      updated_at = now()
    WHERE id = v_physical_id;
  END IF;

  SELECT rs.id INTO v_bga_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'BGA implementation'
    AND COALESCE(rs.platform, '') = 'Board Game Arena'
    AND COALESCE(rs.revision_label, '') = '260623-1715'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_bga_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'BGA implementation',
      'Board Game Arena Release 260623-1715; audited 2026-08-22',
      true, '260623-1715', 'Board Game Arena', 'ATM Gaming', 'active',
      'source_bound', ARRAY['bga:pili-pili:260623-1715']::text[]
    ) RETURNING id INTO v_bga_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Board Game Arena Release 260623-1715; audited 2026-08-22',
      is_active = true,
      publisher_name = 'ATM Gaming',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY['bga:pili-pili:260623-1715']::text[],
      updated_at = now()
    WHERE id = v_bga_id;
  END IF;

  INSERT INTO public.claims (
    claim_id, rule_set_id, claim_type, normalized_payload, target_type,
    field_path, lifecycle_status, generator_provenance
  ) VALUES
    (
      'pili-pili:physical:mission-count', v_physical_id, 'component_count',
      '{"value":40,"component":"mission_cards"}'::jsonb, 'game_metadata',
      'components.mission_cards', 'accepted', '{"method":"reviewed_primary_source"}'::jsonb
    ),
    (
      'pili-pili:physical:numbered-count', v_physical_id, 'component_count',
      '{"value":55,"component":"numbered_cards"}'::jsonb, 'game_metadata',
      'components.numbered_cards', 'accepted', '{"method":"reviewed_primary_source"}'::jsonb
    ),
    (
      'pili-pili:physical:joker-count', v_physical_id, 'component_count',
      '{"value":1,"component":"joker"}'::jsonb, 'game_metadata',
      'components.joker', 'accepted', '{"method":"reviewed_primary_source"}'::jsonb
    ),
    (
      'pili-pili:physical:pili-count-overview', v_physical_id, 'component_count',
      '{"value":23,"component":"pili_cards"}'::jsonb, 'game_metadata',
      'components.pili_cards', 'candidate', '{"method":"reviewed_primary_source","conflict":"same_publisher_page_disagrees"}'::jsonb
    ),
    (
      'pili-pili:physical:pili-count-faq', v_physical_id, 'component_count',
      '{"value":22,"component":"pili_cards","form":"double-sided"}'::jsonb, 'game_metadata',
      'components.pili_cards', 'candidate', '{"method":"reviewed_primary_source","conflict":"same_publisher_page_disagrees"}'::jsonb
    ),
    (
      'pili-pili:bga:mission-count', v_bga_id, 'component_count',
      '{"value":36,"component":"mission_cards"}'::jsonb, 'game_metadata',
      'components.mission_cards', 'accepted', '{"method":"reviewed_authorized_platform_source"}'::jsonb
    ),
    (
      'pili-pili:bga:pili-count', v_bga_id, 'component_count',
      '{"value":17,"component":"pili_cards"}'::jsonb, 'game_metadata',
      'components.pili_cards', 'accepted', '{"method":"reviewed_authorized_platform_source"}'::jsonb
    ),
    (
      'pili-pili:bga:end-threshold', v_bga_id, 'game_end_condition',
      '{"pili_threshold":6,"winner":"fewest_pili"}'::jsonb, 'game_metadata',
      'rules.game_end', 'accepted', '{"method":"reviewed_authorized_platform_source"}'::jsonb
    ),
    (
      'pili-pili:bga:last-bid-constraint', v_bga_id, 'rule_statement',
      '{"rule":"final bidder cannot make total bids equal tricks available"}'::jsonb, 'game_metadata',
      'rules.bidding.last_bid_constraint', 'accepted', '{"method":"reviewed_authorized_platform_source"}'::jsonb
    ),
    (
      'pili-pili:bga:joker-range', v_bga_id, 'rule_statement',
      '{"min":0,"max":56}'::jsonb, 'game_metadata',
      'rules.joker.declared_value_range', 'accepted', '{"method":"reviewed_authorized_platform_source"}'::jsonb
    ),
    (
      'pili-pili:bga:penalty', v_bga_id, 'rule_statement',
      '{"formula":"absolute_difference","operands":["bid","tricks_won"]}'::jsonb, 'game_metadata',
      'rules.penalty', 'accepted', '{"method":"reviewed_authorized_platform_source"}'::jsonb
    )
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
    binding_id, claim_id, source_id, locator_id, relation, reviewer_provenance, verified_at
  ) VALUES
    ('pili-pili:physical:mission-count:support', 'pili-pili:physical:mission-count', 'publisher:atm:pili-pili:current', 'pili-pili:publisher:card-overview', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:physical:numbered-count:support', 'pili-pili:physical:numbered-count', 'publisher:atm:pili-pili:current', 'pili-pili:publisher:card-overview', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:physical:joker-count:support', 'pili-pili:physical:joker-count', 'publisher:atm:pili-pili:current', 'pili-pili:publisher:card-overview', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:physical:pili-23:support', 'pili-pili:physical:pili-count-overview', 'publisher:atm:pili-pili:current', 'pili-pili:publisher:card-overview', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:physical:pili-23:faq-contradiction', 'pili-pili:physical:pili-count-overview', 'publisher:atm:pili-pili:current', 'pili-pili:publisher:faq-box', 'contradicts', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:physical:pili-22:support', 'pili-pili:physical:pili-count-faq', 'publisher:atm:pili-pili:current', 'pili-pili:publisher:faq-box', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:physical:pili-22:overview-contradiction', 'pili-pili:physical:pili-count-faq', 'publisher:atm:pili-pili:current', 'pili-pili:publisher:card-overview', 'contradicts', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:bga:mission-count:support', 'pili-pili:bga:mission-count', 'bga:pili-pili:260623-1715', 'pili-pili:bga:rules-summary', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:bga:pili-count:support', 'pili-pili:bga:pili-count', 'bga:pili-pili:260623-1715', 'pili-pili:bga:rules-summary', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:bga:end-threshold:support', 'pili-pili:bga:end-threshold', 'bga:pili-pili:260623-1715', 'pili-pili:bga:rules-summary', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:bga:last-bid:support', 'pili-pili:bga:last-bid-constraint', 'bga:pili-pili:260623-1715', 'pili-pili:bga:rules-summary', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:bga:joker-range:support', 'pili-pili:bga:joker-range', 'bga:pili-pili:260623-1715', 'pili-pili:bga:rules-summary', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now()),
    ('pili-pili:bga:penalty:support', 'pili-pili:bga:penalty', 'bga:pili-pili:260623-1715', 'pili-pili:bga:rules-summary', 'supports', '{"reviewed":"2026-08-22"}'::jsonb, now())
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    verified_at = EXCLUDED.verified_at;
END $$;

COMMIT;
