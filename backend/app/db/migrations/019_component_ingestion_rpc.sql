BEGIN;

CREATE OR REPLACE FUNCTION public.apply_component_ingestion_v1(payload jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
DECLARE
  v_item jsonb;
  v_game_id uuid;
  v_rule_set_id uuid;
  v_catalog_id uuid;
  v_source_ids text[];
  v_enum_values text[];
  v_claim_id text;
  v_binding_id text;
BEGIN
  IF COALESCE(payload->>'schema_version', '') <> '1.0' THEN
    RAISE EXCEPTION 'unsupported component ingestion schema_version';
  END IF;
  IF COALESCE(payload->>'game_slug', '') = '' OR COALESCE(payload->>'ruleset_id', '') = '' THEN
    RAISE EXCEPTION 'game_slug and ruleset_id are required';
  END IF;

  v_rule_set_id := (payload->>'ruleset_id')::uuid;
  SELECT g.id
    INTO v_game_id
  FROM public.games g
  JOIN public.rule_sets rs ON rs.game_id = g.id
  WHERE g.slug = payload->>'game_slug'
    AND g.identity_status = 'verified'
    AND rs.id = v_rule_set_id
    AND g.id::text = payload->>'game_id';

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'verified Game / RuleSet binding did not resolve';
  END IF;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'sources', '[]'::jsonb))
  LOOP
    IF EXISTS (
      SELECT 1
      FROM public.evidence_sources es
      WHERE es.source_id = v_item->>'source_id'
        AND es.url IS NOT NULL
        AND v_item->>'url' IS NOT NULL
        AND es.url <> v_item->>'url'
    ) THEN
      RAISE EXCEPTION 'source_id % is already bound to a different URL', v_item->>'source_id';
    END IF;

    INSERT INTO public.evidence_sources (
      source_id, url, source_type, revision_label, trust_metadata
    ) VALUES (
      v_item->>'source_id',
      v_item->>'url',
      v_item->>'source_type',
      NULLIF(v_item->>'revision_label', ''),
      COALESCE(v_item->'trust_metadata', '{}'::jsonb)
    )
    ON CONFLICT (source_id) DO UPDATE SET
      url = COALESCE(public.evidence_sources.url, EXCLUDED.url),
      source_type = EXCLUDED.source_type,
      revision_label = COALESCE(EXCLUDED.revision_label, public.evidence_sources.revision_label),
      trust_metadata = public.evidence_sources.trust_metadata || EXCLUDED.trust_metadata,
      updated_at = now();
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'source_locators', '[]'::jsonb))
  LOOP
    IF EXISTS (
      SELECT 1
      FROM public.source_locators sl
      WHERE sl.locator_id = v_item->>'locator_id'
        AND sl.source_id <> v_item->>'source_id'
    ) THEN
      RAISE EXCEPTION 'locator_id % is already bound to a different source', v_item->>'locator_id';
    END IF;

    INSERT INTO public.source_locators (
      locator_id, source_id, page_number, section_heading, anchor, selector,
      structured_path, external_reference
    ) VALUES (
      v_item->>'locator_id',
      v_item->>'source_id',
      NULLIF(v_item->>'page_number', '')::integer,
      NULLIF(v_item->>'section_heading', ''),
      NULLIF(v_item->>'anchor', ''),
      NULLIF(v_item->>'selector', ''),
      NULLIF(v_item->>'structured_path', ''),
      NULLIF(v_item->>'external_reference', '')
    )
    ON CONFLICT (locator_id) DO UPDATE SET
      page_number = EXCLUDED.page_number,
      section_heading = EXCLUDED.section_heading,
      anchor = EXCLUDED.anchor,
      selector = EXCLUDED.selector,
      structured_path = EXCLUDED.structured_path,
      external_reference = EXCLUDED.external_reference;
  END LOOP;

  INSERT INTO public.component_catalogs (rule_set_id, schema_version, metadata)
  VALUES (
    v_rule_set_id,
    payload->>'schema_version',
    COALESCE(payload->'catalog_metadata', '{}'::jsonb)
  )
  ON CONFLICT (rule_set_id) DO UPDATE SET
    schema_version = EXCLUDED.schema_version,
    metadata = public.component_catalogs.metadata || EXCLUDED.metadata,
    updated_at = now()
  RETURNING id INTO v_catalog_id;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'component_sets', '[]'::jsonb))
  LOOP
    v_source_ids := ARRAY(SELECT jsonb_array_elements_text(COALESCE(v_item->'source_ids', '[]'::jsonb)));
    INSERT INTO public.component_sets (
      catalog_id, rule_set_id, component_set_id, canonical_name, kind,
      parent_component_set_id, verification_status, source_ids, metadata
    ) VALUES (
      v_catalog_id,
      v_rule_set_id,
      v_item->>'component_set_id',
      v_item->>'canonical_name',
      NULLIF(v_item->>'kind', ''),
      NULLIF(v_item->>'parent_component_set_id', ''),
      COALESCE(v_item->>'verification_status', 'unknown'),
      v_source_ids,
      COALESCE(v_item->'metadata', '{}'::jsonb)
    )
    ON CONFLICT (rule_set_id, component_set_id) DO UPDATE SET
      catalog_id = EXCLUDED.catalog_id,
      canonical_name = EXCLUDED.canonical_name,
      kind = EXCLUDED.kind,
      parent_component_set_id = EXCLUDED.parent_component_set_id,
      verification_status = EXCLUDED.verification_status,
      source_ids = EXCLUDED.source_ids,
      metadata = public.component_sets.metadata || EXCLUDED.metadata,
      updated_at = now();
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'property_definitions', '[]'::jsonb))
  LOOP
    v_source_ids := ARRAY(SELECT jsonb_array_elements_text(COALESCE(v_item->'source_ids', '[]'::jsonb)));
    v_enum_values := ARRAY(SELECT jsonb_array_elements_text(COALESCE(v_item->'enum_values', '[]'::jsonb)));
    INSERT INTO public.component_property_definitions (
      catalog_id, rule_set_id, property_key, labels, value_type, cardinality,
      unit, enum_values, filterable, sortable, verification_status, source_ids, metadata
    ) VALUES (
      v_catalog_id,
      v_rule_set_id,
      v_item->>'property_key',
      COALESCE(v_item->'labels', '{}'::jsonb),
      v_item->>'value_type',
      COALESCE(v_item->>'cardinality', 'one'),
      NULLIF(v_item->>'unit', ''),
      v_enum_values,
      COALESCE((v_item->>'filterable')::boolean, false),
      COALESCE((v_item->>'sortable')::boolean, false),
      COALESCE(v_item->>'verification_status', 'unknown'),
      v_source_ids,
      COALESCE(v_item->'metadata', '{}'::jsonb)
    )
    ON CONFLICT (rule_set_id, property_key) DO UPDATE SET
      catalog_id = EXCLUDED.catalog_id,
      labels = EXCLUDED.labels,
      value_type = EXCLUDED.value_type,
      cardinality = EXCLUDED.cardinality,
      unit = EXCLUDED.unit,
      enum_values = EXCLUDED.enum_values,
      filterable = EXCLUDED.filterable,
      sortable = EXCLUDED.sortable,
      verification_status = EXCLUDED.verification_status,
      source_ids = EXCLUDED.source_ids,
      metadata = public.component_property_definitions.metadata || EXCLUDED.metadata,
      updated_at = now();
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'components', '[]'::jsonb))
  LOOP
    v_source_ids := ARRAY(SELECT jsonb_array_elements_text(COALESCE(v_item->'source_ids', '[]'::jsonb)));
    INSERT INTO public.components (
      catalog_id, rule_set_id, component_id, component_set_id, canonical_name,
      kind, quantity, verification_status, source_ids, metadata
    ) VALUES (
      v_catalog_id,
      v_rule_set_id,
      v_item->>'component_id',
      NULLIF(v_item->>'component_set_id', ''),
      v_item->>'canonical_name',
      v_item->>'kind',
      NULLIF(v_item->>'quantity', '')::integer,
      COALESCE(v_item->>'verification_status', 'unknown'),
      v_source_ids,
      COALESCE(v_item->'metadata', '{}'::jsonb)
    )
    ON CONFLICT (rule_set_id, component_id) DO UPDATE SET
      catalog_id = EXCLUDED.catalog_id,
      component_set_id = EXCLUDED.component_set_id,
      canonical_name = EXCLUDED.canonical_name,
      kind = EXCLUDED.kind,
      quantity = EXCLUDED.quantity,
      verification_status = EXCLUDED.verification_status,
      source_ids = EXCLUDED.source_ids,
      metadata = public.components.metadata || EXCLUDED.metadata,
      updated_at = now();
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'component_properties', '[]'::jsonb))
  LOOP
    v_source_ids := ARRAY(SELECT jsonb_array_elements_text(COALESCE(v_item->'source_ids', '[]'::jsonb)));
    INSERT INTO public.component_properties (
      rule_set_id, component_id, property_key, value_type, cardinality, ordinal,
      text_value, integer_value, number_value, boolean_value, enum_value,
      concept_ref_id, component_ref_id, verification_status, source_ids, metadata
    ) VALUES (
      v_rule_set_id,
      v_item->>'component_id',
      v_item->>'property_key',
      v_item->>'value_type',
      v_item->>'cardinality',
      (v_item->>'ordinal')::integer,
      NULLIF(v_item->>'text_value', ''),
      NULLIF(v_item->>'integer_value', '')::bigint,
      NULLIF(v_item->>'number_value', '')::double precision,
      NULLIF(v_item->>'boolean_value', '')::boolean,
      NULLIF(v_item->>'enum_value', ''),
      NULLIF(v_item->>'concept_ref_id', ''),
      NULLIF(v_item->>'component_ref_id', ''),
      COALESCE(v_item->>'verification_status', 'unknown'),
      v_source_ids,
      COALESCE(v_item->'metadata', '{}'::jsonb)
    )
    ON CONFLICT (rule_set_id, component_id, property_key, ordinal) DO UPDATE SET
      value_type = EXCLUDED.value_type,
      cardinality = EXCLUDED.cardinality,
      text_value = EXCLUDED.text_value,
      integer_value = EXCLUDED.integer_value,
      number_value = EXCLUDED.number_value,
      boolean_value = EXCLUDED.boolean_value,
      enum_value = EXCLUDED.enum_value,
      concept_ref_id = EXCLUDED.concept_ref_id,
      component_ref_id = EXCLUDED.component_ref_id,
      verification_status = EXCLUDED.verification_status,
      source_ids = EXCLUDED.source_ids,
      metadata = public.component_properties.metadata || EXCLUDED.metadata;
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'component_abilities', '[]'::jsonb))
  LOOP
    v_source_ids := ARRAY(SELECT jsonb_array_elements_text(COALESCE(v_item->'source_ids', '[]'::jsonb)));
    INSERT INTO public.component_abilities (
      rule_set_id, component_id, ability_id, printed_text, normalized_label,
      verification_status, source_ids, metadata
    ) VALUES (
      v_rule_set_id,
      v_item->>'component_id',
      v_item->>'ability_id',
      NULLIF(v_item->>'printed_text', ''),
      NULLIF(v_item->>'normalized_label', ''),
      COALESCE(v_item->>'verification_status', 'unknown'),
      v_source_ids,
      COALESCE(v_item->'metadata', '{}'::jsonb)
    )
    ON CONFLICT (rule_set_id, ability_id) DO UPDATE SET
      component_id = EXCLUDED.component_id,
      printed_text = EXCLUDED.printed_text,
      normalized_label = EXCLUDED.normalized_label,
      verification_status = EXCLUDED.verification_status,
      source_ids = EXCLUDED.source_ids,
      metadata = public.component_abilities.metadata || EXCLUDED.metadata,
      updated_at = now();
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'component_concepts', '[]'::jsonb))
  LOOP
    INSERT INTO public.component_concepts (rule_set_id, component_id, concept_id, reference_kind)
    VALUES (v_rule_set_id, v_item->>'component_id', v_item->>'concept_id', COALESCE(v_item->>'reference_kind', 'classifies'))
    ON CONFLICT DO NOTHING;
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'component_rule_nodes', '[]'::jsonb))
  LOOP
    INSERT INTO public.component_rule_nodes (rule_set_id, component_id, rule_id, reference_kind)
    VALUES (v_rule_set_id, v_item->>'component_id', v_item->>'rule_id', COALESCE(v_item->>'reference_kind', 'governed_by'))
    ON CONFLICT DO NOTHING;
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'ability_concepts', '[]'::jsonb))
  LOOP
    INSERT INTO public.component_ability_concepts (rule_set_id, ability_id, concept_id)
    VALUES (v_rule_set_id, v_item->>'ability_id', v_item->>'concept_id')
    ON CONFLICT DO NOTHING;
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'ability_rule_nodes', '[]'::jsonb))
  LOOP
    INSERT INTO public.component_ability_rule_nodes (rule_set_id, ability_id, rule_id)
    VALUES (v_rule_set_id, v_item->>'ability_id', v_item->>'rule_id')
    ON CONFLICT DO NOTHING;
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'claims', '[]'::jsonb))
  LOOP
    v_claim_id := v_item->>'claim_id';
    IF EXISTS (
      SELECT 1
      FROM public.claims c
      WHERE c.claim_id = v_claim_id
        AND (
          c.rule_set_id <> v_rule_set_id OR
          c.target_type <> v_item->>'target_type' OR
          c.rule_id IS DISTINCT FROM NULLIF(v_item->>'rule_id', '') OR
          c.component_id IS DISTINCT FROM NULLIF(v_item->>'component_id', '') OR
          c.component_set_id IS DISTINCT FROM NULLIF(v_item->>'component_set_id', '') OR
          c.property_key IS DISTINCT FROM NULLIF(v_item->>'property_key', '') OR
          c.ordinal IS DISTINCT FROM NULLIF(v_item->>'ordinal', '')::integer OR
          c.ability_id IS DISTINCT FROM NULLIF(v_item->>'ability_id', '') OR
          c.field_path IS DISTINCT FROM NULLIF(v_item->>'field_path', '')
        )
    ) THEN
      RAISE EXCEPTION 'claim_id % collides with a different target', v_claim_id;
    END IF;

    INSERT INTO public.claims (
      claim_id, rule_set_id, claim_type, normalized_payload, target_type,
      rule_id, component_id, component_set_id, property_key, ordinal, ability_id, field_path,
      lifecycle_status, generator_provenance
    ) VALUES (
      v_claim_id,
      v_rule_set_id,
      v_item->>'claim_type',
      COALESCE(v_item->'normalized_payload', '{}'::jsonb),
      v_item->>'target_type',
      NULLIF(v_item->>'rule_id', ''),
      NULLIF(v_item->>'component_id', ''),
      NULLIF(v_item->>'component_set_id', ''),
      NULLIF(v_item->>'property_key', ''),
      NULLIF(v_item->>'ordinal', '')::integer,
      NULLIF(v_item->>'ability_id', ''),
      NULLIF(v_item->>'field_path', ''),
      COALESCE(v_item->>'lifecycle_status', 'candidate'),
      COALESCE(v_item->'generator_provenance', '{}'::jsonb)
    )
    ON CONFLICT (claim_id) DO UPDATE SET
      claim_type = EXCLUDED.claim_type,
      normalized_payload = EXCLUDED.normalized_payload,
      lifecycle_status = EXCLUDED.lifecycle_status,
      generator_provenance = public.claims.generator_provenance || EXCLUDED.generator_provenance,
      updated_at = now();
  END LOOP;

  FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(payload->'evidence_bindings', '[]'::jsonb))
  LOOP
    v_binding_id := v_item->>'binding_id';
    IF EXISTS (
      SELECT 1
      FROM public.evidence_bindings eb
      WHERE eb.binding_id = v_binding_id
        AND (
          eb.claim_id <> v_item->>'claim_id' OR
          eb.source_id <> v_item->>'source_id' OR
          eb.locator_id IS DISTINCT FROM NULLIF(v_item->>'locator_id', '') OR
          eb.relation <> v_item->>'relation'
        )
    ) THEN
      RAISE EXCEPTION 'binding_id % collides with a different evidence relation', v_binding_id;
    END IF;

    INSERT INTO public.evidence_bindings (
      binding_id, claim_id, source_id, locator_id, relation,
      reviewer_provenance, generator_provenance
    ) VALUES (
      v_binding_id,
      v_item->>'claim_id',
      v_item->>'source_id',
      NULLIF(v_item->>'locator_id', ''),
      v_item->>'relation',
      COALESCE(v_item->'reviewer_provenance', '{}'::jsonb),
      COALESCE(v_item->'generator_provenance', '{}'::jsonb)
    )
    ON CONFLICT (binding_id) DO UPDATE SET
      reviewer_provenance = public.evidence_bindings.reviewer_provenance || EXCLUDED.reviewer_provenance,
      generator_provenance = public.evidence_bindings.generator_provenance || EXCLUDED.generator_provenance;
  END LOOP;

  RETURN jsonb_build_object(
    'ruleset_id', v_rule_set_id::text,
    'catalog_id', v_catalog_id::text,
    'persisted', jsonb_build_object(
      'component_sets', (SELECT count(*) FROM public.component_sets cs WHERE cs.rule_set_id = v_rule_set_id),
      'property_definitions', (SELECT count(*) FROM public.component_property_definitions pd WHERE pd.rule_set_id = v_rule_set_id),
      'components', (SELECT count(*) FROM public.components c WHERE c.rule_set_id = v_rule_set_id),
      'component_properties', (SELECT count(*) FROM public.component_properties cp WHERE cp.rule_set_id = v_rule_set_id),
      'component_abilities', (SELECT count(*) FROM public.component_abilities ca WHERE ca.rule_set_id = v_rule_set_id),
      'claims', (SELECT count(*) FROM public.claims c WHERE c.rule_set_id = v_rule_set_id)
    )
  );
END;
$$;

REVOKE ALL ON FUNCTION public.apply_component_ingestion_v1(jsonb) FROM PUBLIC;
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    REVOKE ALL ON FUNCTION public.apply_component_ingestion_v1(jsonb) FROM anon;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    REVOKE ALL ON FUNCTION public.apply_component_ingestion_v1(jsonb) FROM authenticated;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    GRANT EXECUTE ON FUNCTION public.apply_component_ingestion_v1(jsonb) TO service_role;
  END IF;
END $$;

COMMIT;
