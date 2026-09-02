BEGIN;

-- Keep optional Advanced Play separate from the base Skull King RuleSet.
-- The current publisher rulebook and FAQ agree on who leads after a Kraken.
-- A publisher-hosted player reference card shows the conflicting wording that
-- the FAQ identifies as a discrepancy from one print run. The exact print run
-- of the hosted image is not inferred here.
-- Keep this variant inactive until the public UI explicitly selects variants;
-- canonical SSR currently scans every active source-bound RuleSet.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES (
  'publisher:grandpa-becks:skull-king:advanced-player-reference',
  'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/SK_Advanced_Rules.jpg?v=1672938216',
  'Grandpa Beck''s Games Skull King Advanced Rules player reference card',
  'player_reference_card',
  'Grandpa Beck''s Games',
  'physical',
  'en',
  'asset-1672938216',
  '{"authority":"publisher","role":"player_reference_card","scope":"advanced_play","audit_date":"2026-09-03","print_run":"unresolved","notes":"The current publisher Skull King rules page links this asset. The publisher FAQ says one print run had a Kraken discrepancy, but does not identify this asset by print-run number."}'::jsonb
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
  (
    'skull-king:rulebook:advanced-kraken',
    'publisher:grandpa-becks:skull-king:current-rulebook',
    16,
    'ADVANCED PLAY / The Kraken',
    'Kraken destroys the trick; the next trick is led by the player who would have won that trick.'
  ),
  (
    'skull-king:player-reference:advanced-kraken',
    'publisher:grandpa-becks:skull-king:advanced-player-reference',
    NULL,
    'ADVANCED RULES / KRAKEN',
    'The player reference instead says the player to the left of the Kraken player leads next.'
  ),
  (
    'skull-king:faq:kraken-next-lead',
    'publisher:grandpa-becks:skull-king:current-rules-faq',
    NULL,
    'FAQ / When the Kraken is played, who leads off the next trick?',
    'The publisher acknowledges a rulebook/player-aid discrepancy in one print run and confirms that the player who would have won without the Kraken leads next.'
  )
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
  page_number = EXCLUDED.page_number,
  section_heading = EXCLUDED.section_heading,
  external_reference = EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_work_id uuid;
  v_base_ruleset_id uuid;
  v_advanced_ruleset_id uuid;
BEGIN
  SELECT g.id, g.work_id
    INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'skull-king'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Skull King Game/Work row is required before applying the Kraken clarification';
  END IF;

  SELECT rs.id
    INTO v_base_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND rs.is_active = true
    AND rs.status = 'active'
    AND rs.verification_status = 'source_bound'
    AND COALESCE(rs.language_code, '') = 'en'
    AND COALESCE(rs.edition_label, '') = 'Grandpa Beck''s Games current edition'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = 'current-web-rulebook-1764178570'
    AND COALESCE(rs.variant_label, '') = ''
  ORDER BY rs.version DESC
  LIMIT 1;

  IF v_base_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Skull King base RuleSet is required before applying the Kraken clarification';
  END IF;

  SELECT rs.id
    INTO v_advanced_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'en'
    AND COALESCE(rs.edition_label, '') = 'Grandpa Beck''s Games current edition'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = 'current-web-rulebook-1764178570'
    AND COALESCE(rs.variant_label, '') = 'Advanced Play'
    AND rs.version = 1
  LIMIT 1;

  IF v_advanced_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, base_rule_set_id, relation_type, variant_label,
      source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'en', 'Grandpa Beck''s Games current edition',
      'current English rulebook web revision 1764178570; current FAQ and Advanced Rules player reference audited 2026-09-03',
      false, 'current-web-rulebook-1764178570', 'physical', 'Grandpa Beck''s Games',
      'draft', 'source_bound', v_base_ruleset_id, 'variant_of', 'Advanced Play',
      ARRAY[
        'publisher:grandpa-becks:skull-king:current-rulebook',
        'publisher:grandpa-becks:skull-king:current-rules-faq',
        'publisher:grandpa-becks:skull-king:advanced-player-reference'
      ]::text[]
    )
    RETURNING id INTO v_advanced_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'current English rulebook web revision 1764178570; current FAQ and Advanced Rules player reference audited 2026-09-03',
      is_active = false,
      publisher_name = 'Grandpa Beck''s Games',
      status = 'draft',
      verification_status = 'source_bound',
      base_rule_set_id = v_base_ruleset_id,
      relation_type = 'variant_of',
      source_ids = ARRAY[
        'publisher:grandpa-becks:skull-king:current-rulebook',
        'publisher:grandpa-becks:skull-king:current-rules-faq',
        'publisher:grandpa-becks:skull-king:advanced-player-reference'
      ]::text[],
      updated_at = now()
    WHERE id = v_advanced_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES (
    v_advanced_ruleset_id,
    'advanced.kraken.next-lead',
    'effect',
    'Krakenを出すとそのトリックは破棄され、誰もトリックを取らない。次のトリックは、Krakenが出なかった場合にそのトリックへ勝っていたプレイヤーがリードする。',
    0,
    'source_bound',
    'skull-king:advanced:rule:kraken.next-lead.current',
    'skull-king:advanced:binding:kraken.next-lead.rulebook',
    'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570',
    'skull-king:rulebook:advanced-kraken',
    '{"scope":"advanced_play","source_language":"en","normalized_language":"ja","optional":true}'::jsonb
  )
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
  ) VALUES
    (
      'skull-king:advanced:rule:kraken.next-lead.current',
      v_advanced_ruleset_id,
      'rule_statement',
      jsonb_build_object(
        'statement', 'Krakenを出すとそのトリックは破棄され、誰もトリックを取らない。次のトリックは、Krakenが出なかった場合にそのトリックへ勝っていたプレイヤーがリードする。',
        'source_scope', 'advanced_play'
      ),
      'rule_node',
      'advanced.kraken.next-lead',
      'accepted',
      '{"seed":"125_add_skull_king_kraken_clarification","audit_date":"2026-09-03","method":"manual_primary_source_normalization"}'::jsonb
    ),
    (
      'skull-king:advanced:rule:kraken.next-lead.player-aid',
      v_advanced_ruleset_id,
      'rule_statement',
      jsonb_build_object(
        'statement', 'Krakenを出した場合、そのトリックを破棄し、Krakenを出したプレイヤーの左隣のプレイヤーが次のトリックをリードする。',
        'source_scope', 'advanced_play',
        'print_run', 'unresolved'
      ),
      'rule_node',
      'advanced.kraken.next-lead',
      'rejected',
      '{"seed":"125_add_skull_king_kraken_clarification","audit_date":"2026-09-03","method":"manual_primary_source_conflict_preservation"}'::jsonb
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
    (
      'skull-king:advanced:binding:kraken.next-lead.rulebook',
      'skull-king:advanced:rule:kraken.next-lead.current',
      'publisher:grandpa-becks:skull-king:current-rulebook',
      'skull-king:rulebook:advanced-kraken',
      'supports',
      '{"audit_date":"2026-09-03","method":"manual_primary_source_verification"}'::jsonb,
      '{"seed":"125_add_skull_king_kraken_clarification"}'::jsonb,
      now()
    ),
    (
      'skull-king:advanced:binding:kraken.next-lead.faq',
      'skull-king:advanced:rule:kraken.next-lead.current',
      'publisher:grandpa-becks:skull-king:current-rules-faq',
      'skull-king:faq:kraken-next-lead',
      'supports',
      '{"audit_date":"2026-09-03","method":"manual_primary_source_verification"}'::jsonb,
      '{"seed":"125_add_skull_king_kraken_clarification"}'::jsonb,
      now()
    ),
    (
      'skull-king:advanced:binding:kraken.next-lead.player-aid',
      'skull-king:advanced:rule:kraken.next-lead.player-aid',
      'publisher:grandpa-becks:skull-king:advanced-player-reference',
      'skull-king:player-reference:advanced-kraken',
      'supports',
      '{"audit_date":"2026-09-03","method":"manual_primary_source_verification","print_run":"unresolved"}'::jsonb,
      '{"seed":"125_add_skull_king_kraken_clarification"}'::jsonb,
      now()
    ),
    (
      'skull-king:advanced:binding:kraken.next-lead.player-aid-vs-rulebook',
      'skull-king:advanced:rule:kraken.next-lead.player-aid',
      'publisher:grandpa-becks:skull-king:current-rulebook',
      'skull-king:rulebook:advanced-kraken',
      'contradicts',
      '{"audit_date":"2026-09-03","method":"manual_primary_source_verification"}'::jsonb,
      '{"seed":"125_add_skull_king_kraken_clarification"}'::jsonb,
      now()
    ),
    (
      'skull-king:advanced:binding:kraken.next-lead.player-aid-vs-faq',
      'skull-king:advanced:rule:kraken.next-lead.player-aid',
      'publisher:grandpa-becks:skull-king:current-rules-faq',
      'skull-king:faq:kraken-next-lead',
      'contradicts',
      '{"audit_date":"2026-09-03","method":"manual_primary_source_verification"}'::jsonb,
      '{"seed":"125_add_skull_king_kraken_clarification"}'::jsonb,
      now()
    )
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
