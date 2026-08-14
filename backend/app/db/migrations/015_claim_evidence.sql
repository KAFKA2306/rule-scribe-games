BEGIN;

CREATE TABLE IF NOT EXISTS public.evidence_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id text NOT NULL UNIQUE CHECK (source_id ~ '^[a-z0-9][a-z0-9._:-]{2,191}$'),
  url text,
  document_identity text,
  source_type text NOT NULL CHECK (btrim(source_type) <> ''),
  publisher_name text,
  platform text,
  language_code text,
  revision_label text,
  published_at timestamptz,
  retrieved_at timestamptz,
  trust_metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(trust_metadata) = 'object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (COALESCE(btrim(url), '') <> '' OR COALESCE(btrim(document_identity), '') <> '')
);

CREATE TABLE IF NOT EXISTS public.source_locators (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  locator_id text NOT NULL UNIQUE CHECK (locator_id ~ '^[a-z0-9][a-z0-9._:-]{2,191}$'),
  source_id text NOT NULL REFERENCES public.evidence_sources(source_id) ON DELETE CASCADE,
  page_number integer CHECK (page_number IS NULL OR page_number >= 1),
  section_heading text,
  anchor text,
  selector text,
  structured_path text,
  external_reference text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    page_number IS NOT NULL OR
    COALESCE(btrim(section_heading), '') <> '' OR
    COALESCE(btrim(anchor), '') <> '' OR
    COALESCE(btrim(selector), '') <> '' OR
    COALESCE(btrim(structured_path), '') <> '' OR
    COALESCE(btrim(external_reference), '') <> ''
  ),
  UNIQUE (source_id, locator_id)
);

CREATE TABLE IF NOT EXISTS public.claims (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  claim_id text NOT NULL UNIQUE CHECK (claim_id ~ '^[a-z0-9][a-z0-9._:-]{2,191}$'),
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  claim_type text NOT NULL CHECK (btrim(claim_type) <> ''),
  normalized_payload jsonb NOT NULL CHECK (jsonb_typeof(normalized_payload) = 'object'),
  target_type text NOT NULL CHECK (
    target_type IN ('rule_node','component_property','ability_printed_text','ability_normalized','game_metadata')
  ),
  rule_id text,
  component_id text,
  property_key text,
  ordinal integer CHECK (ordinal IS NULL OR ordinal >= 0),
  ability_id text,
  field_path text,
  lifecycle_status text NOT NULL DEFAULT 'unknown' CHECK (
    lifecycle_status IN ('unknown','candidate','accepted','rejected')
  ),
  generator_provenance jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(generator_provenance) = 'object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT claims_rule_node_target_fkey
    FOREIGN KEY (rule_set_id, rule_id)
    REFERENCES public.rule_nodes(rule_set_id, rule_id)
    ON DELETE CASCADE,
  CONSTRAINT claims_component_property_target_fkey
    FOREIGN KEY (rule_set_id, component_id, property_key, ordinal)
    REFERENCES public.component_properties(rule_set_id, component_id, property_key, ordinal)
    ON DELETE CASCADE,
  CONSTRAINT claims_ability_target_fkey
    FOREIGN KEY (rule_set_id, ability_id)
    REFERENCES public.component_abilities(rule_set_id, ability_id)
    ON DELETE CASCADE,
  CHECK (
    (
      target_type = 'rule_node' AND rule_id IS NOT NULL AND
      component_id IS NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NULL AND field_path IS NULL
    ) OR
    (
      target_type = 'component_property' AND rule_id IS NULL AND
      component_id IS NOT NULL AND property_key IS NOT NULL AND ordinal IS NOT NULL AND
      ability_id IS NULL AND field_path IS NULL
    ) OR
    (
      target_type IN ('ability_printed_text','ability_normalized') AND rule_id IS NULL AND
      component_id IS NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NOT NULL AND field_path IS NULL
    ) OR
    (
      target_type = 'game_metadata' AND rule_id IS NULL AND
      component_id IS NULL AND property_key IS NULL AND ordinal IS NULL AND
      ability_id IS NULL AND COALESCE(btrim(field_path), '') <> ''
    )
  )
);

CREATE TABLE IF NOT EXISTS public.evidence_bindings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  binding_id text NOT NULL UNIQUE CHECK (binding_id ~ '^[a-z0-9][a-z0-9._:-]{2,191}$'),
  claim_id text NOT NULL REFERENCES public.claims(claim_id) ON DELETE CASCADE,
  source_id text NOT NULL REFERENCES public.evidence_sources(source_id) ON DELETE RESTRICT,
  locator_id text,
  relation text NOT NULL CHECK (relation IN ('supports','contradicts','contextualizes','unresolved')),
  reviewer_provenance jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(reviewer_provenance) = 'object'),
  generator_provenance jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(generator_provenance) = 'object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  verified_at timestamptz,
  CONSTRAINT evidence_bindings_locator_fkey
    FOREIGN KEY (source_id, locator_id)
    REFERENCES public.source_locators(source_id, locator_id)
    ON DELETE RESTRICT,
  UNIQUE (claim_id, source_id, locator_id, relation)
);

CREATE INDEX IF NOT EXISTS claims_ruleset_target_idx
  ON public.claims (rule_set_id, target_type);
CREATE INDEX IF NOT EXISTS claims_rule_node_idx
  ON public.claims (rule_set_id, rule_id)
  WHERE target_type = 'rule_node';
CREATE INDEX IF NOT EXISTS claims_component_property_idx
  ON public.claims (rule_set_id, component_id, property_key, ordinal)
  WHERE target_type = 'component_property';
CREATE INDEX IF NOT EXISTS claims_ability_idx
  ON public.claims (rule_set_id, ability_id, target_type)
  WHERE ability_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS evidence_bindings_claim_idx
  ON public.evidence_bindings (claim_id, relation);
CREATE INDEX IF NOT EXISTS evidence_bindings_source_idx
  ON public.evidence_bindings (source_id, relation);

ALTER TABLE public.evidence_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.source_locators ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_bindings ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE VIEW public.claim_evidence_audit_summary
WITH (security_invoker = true) AS
SELECT
  (SELECT count(*) FROM public.evidence_sources) AS sources,
  (SELECT count(*) FROM public.source_locators) AS source_locators,
  (SELECT count(*) FROM public.claims) AS claims,
  (SELECT count(*) FROM public.evidence_bindings) AS bindings,
  (SELECT count(*) FROM public.evidence_bindings WHERE relation = 'supports') AS supporting_bindings,
  (SELECT count(*) FROM public.evidence_bindings WHERE relation = 'contradicts') AS contradicting_bindings,
  (SELECT count(*) FROM public.claims c WHERE NOT EXISTS (
    SELECT 1 FROM public.evidence_bindings eb WHERE eb.claim_id = c.claim_id AND eb.relation = 'supports'
  )) AS claims_without_support;

COMMIT;
