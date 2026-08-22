BEGIN;

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:arclight:tm-dice:revised-2024-05-30',
    'https://arclightgames.jp/wp-content/uploads/2024/04/TM_DICEGAME_RULES-JPN-fix-2023Dec-for-Web-2.pdf',
    'Terraforming Mars: The Dice Game Japanese revised rulebook',
    'publisher_rulebook',
    'Arclight Games',
    'physical',
    'ja',
    '2024-05-30',
    '{"authority":"publisher","role":"canonical_for_arclight_japanese_revised_rules","audit_date":"2026-08-22"}'::jsonb
  ),
  (
    'publisher:arclight:tm-dice:errata-2024-05-30',
    'https://arclightgames.jp/news/23123/',
    'Arclight errata notice updated 2024-05-30',
    'publisher_errata',
    'Arclight Games',
    'physical',
    'ja',
    '2024-05-30',
    '{"authority":"publisher","role":"errata_for_arclight_japanese_revised_rules","audit_date":"2026-08-22"}'::jsonb
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
    'tm-dice:rulebook:multiplayer-end',
    'publisher:arclight:tm-dice:revised-2024-05-30',
    10,
    'ゲームの終了',
    'Two of the three global parameters trigger the final-turn sequence.'
  ),
  (
    'tm-dice:rulebook:solo',
    'publisher:arclight:tm-dice:revised-2024-05-30',
    11,
    '1人ゲーム',
    'Solo setup, 50-turn limit, and all-three-global-parameters objective.'
  ),
  (
    'tm-dice:errata:time-marker',
    'publisher:arclight:tm-dice:errata-2024-05-30',
    NULL,
    'ルール説明書10ページ、５）時間マーカーの文章',
    '2024-05-30 correction: the marker tracks turns, not rounds, and first advances before the first turn.'
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
  v_ruleset_id uuid;
BEGIN
  SELECT g.id, g.work_id
    INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'terraforming-mars-the-dice-game'
    AND g.identity_status = 'verified'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Verified canonical Terraforming Mars: The Dice Game row is required before RuleSet seed';
  END IF;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'アークライト日本語版 改訂版 第2刷'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2024-05-30'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'アークライト日本語版 改訂版 第2刷',
      'Arclight revised rulebook with 2024-05-30 time-marker correction',
      true, '2024-05-30', 'physical', 'Arclight Games', 'active', 'source_bound',
      ARRAY[
        'publisher:arclight:tm-dice:revised-2024-05-30',
        'publisher:arclight:tm-dice:errata-2024-05-30'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Arclight revised rulebook with 2024-05-30 time-marker correction',
      is_active = true,
      publisher_name = 'Arclight Games',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:arclight:tm-dice:revised-2024-05-30',
        'publisher:arclight:tm-dice:errata-2024-05-30'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.claims (
    claim_id, rule_set_id, claim_type, normalized_payload, target_type,
    field_path, lifecycle_status, generator_provenance
  ) VALUES
    (
      'tm-dice:physical:multiplayer-end', v_ruleset_id, 'game_end_condition',
      '{"global_parameters_required":2,"last_turns":"triggering_player_then_each_other_player"}'::jsonb,
      'game_metadata', 'rules.multiplayer.game_end', 'accepted',
      '{"method":"reviewed_primary_source"}'::jsonb
    ),
    (
      'tm-dice:physical:solo-start', v_ruleset_id, 'setup_rule',
      '{"temperature_c":-28,"oxygen_percent":2}'::jsonb,
      'game_metadata', 'rules.solo.setup.global_parameters', 'accepted',
      '{"method":"reviewed_primary_source"}'::jsonb
    ),
    (
      'tm-dice:physical:solo-turn-limit', v_ruleset_id, 'game_end_condition',
      '{"turns":50}'::jsonb,
      'game_metadata', 'rules.solo.turn_limit', 'accepted',
      '{"method":"reviewed_primary_source"}'::jsonb
    ),
    (
      'tm-dice:physical:solo-end', v_ruleset_id, 'game_end_condition',
      '{"global_parameters_required":3,"score_on_failure":false}'::jsonb,
      'game_metadata', 'rules.solo.game_end', 'accepted',
      '{"method":"reviewed_primary_source"}'::jsonb
    ),
    (
      'tm-dice:physical:time-marker', v_ruleset_id, 'rule_statement',
      '{"unit":"turn","first_advance":"before_first_turn"}'::jsonb,
      'game_metadata', 'rules.solo.time_marker', 'accepted',
      '{"method":"reviewed_primary_source_errata"}'::jsonb
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
    binding_id, claim_id, source_id, locator_id, relation,
    reviewer_provenance, verified_at
  ) VALUES
    (
      'tm-dice:physical:multiplayer-end:support',
      'tm-dice:physical:multiplayer-end',
      'publisher:arclight:tm-dice:revised-2024-05-30',
      'tm-dice:rulebook:multiplayer-end', 'supports',
      '{"reviewed":"2026-08-22"}'::jsonb, now()
    ),
    (
      'tm-dice:physical:solo-start:support',
      'tm-dice:physical:solo-start',
      'publisher:arclight:tm-dice:revised-2024-05-30',
      'tm-dice:rulebook:solo', 'supports',
      '{"reviewed":"2026-08-22"}'::jsonb, now()
    ),
    (
      'tm-dice:physical:solo-turn-limit:support',
      'tm-dice:physical:solo-turn-limit',
      'publisher:arclight:tm-dice:revised-2024-05-30',
      'tm-dice:rulebook:solo', 'supports',
      '{"reviewed":"2026-08-22"}'::jsonb, now()
    ),
    (
      'tm-dice:physical:solo-end:support',
      'tm-dice:physical:solo-end',
      'publisher:arclight:tm-dice:revised-2024-05-30',
      'tm-dice:rulebook:solo', 'supports',
      '{"reviewed":"2026-08-22"}'::jsonb, now()
    ),
    (
      'tm-dice:physical:time-marker:support',
      'tm-dice:physical:time-marker',
      'publisher:arclight:tm-dice:errata-2024-05-30',
      'tm-dice:errata:time-marker', 'supports',
      '{"reviewed":"2026-08-22"}'::jsonb, now()
    )
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    verified_at = EXCLUDED.verified_at;
END $$;

COMMIT;
