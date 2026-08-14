BEGIN;

CREATE TABLE IF NOT EXISTS public.component_catalogs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_set_id uuid NOT NULL UNIQUE REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  schema_version text NOT NULL DEFAULT '1.0',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.component_sets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  catalog_id uuid NOT NULL REFERENCES public.component_catalogs(id) ON DELETE CASCADE,
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  component_set_id text NOT NULL CHECK (component_set_id ~ '^[a-z0-9][a-z0-9._:-]{2,127}$'),
  canonical_name text NOT NULL CHECK (btrim(canonical_name) <> ''),
  kind text CHECK (kind IS NULL OR kind IN ('card','tile','token','die','board','figure','sheet','role','marker','track','other')),
  parent_component_set_id text,
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (verification_status IN ('unknown','source_bound','verified','rejected')),
  source_ids text[] NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rule_set_id, component_set_id),
  CHECK (parent_component_set_id IS NULL OR parent_component_set_id <> component_set_id),
  CHECK (verification_status NOT IN ('source_bound','verified') OR cardinality(source_ids) > 0)
);

ALTER TABLE public.component_sets
  DROP CONSTRAINT IF EXISTS component_sets_parent_fkey;
ALTER TABLE public.component_sets
  ADD CONSTRAINT component_sets_parent_fkey
  FOREIGN KEY (rule_set_id, parent_component_set_id)
  REFERENCES public.component_sets(rule_set_id, component_set_id)
  ON DELETE RESTRICT;

CREATE TABLE IF NOT EXISTS public.component_property_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  catalog_id uuid NOT NULL REFERENCES public.component_catalogs(id) ON DELETE CASCADE,
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  property_key text NOT NULL CHECK (property_key ~ '^[a-z][a-z0-9_.:-]{1,127}$'),
  labels jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(labels) = 'object'),
  value_type text NOT NULL CHECK (value_type IN ('text','integer','number','boolean','enum','concept_ref','component_ref')),
  cardinality text NOT NULL DEFAULT 'one' CHECK (cardinality IN ('one','many')),
  unit text,
  enum_values text[] NOT NULL DEFAULT '{}',
  filterable boolean NOT NULL DEFAULT false,
  sortable boolean NOT NULL DEFAULT false,
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (verification_status IN ('unknown','source_bound','verified','rejected')),
  source_ids text[] NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rule_set_id, property_key),
  UNIQUE (rule_set_id, property_key, value_type, cardinality),
  CHECK ((value_type = 'enum' AND cardinality(enum_values) > 0) OR (value_type <> 'enum' AND cardinality(enum_values) = 0)),
  CHECK (verification_status NOT IN ('source_bound','verified') OR cardinality(source_ids) > 0)
);

CREATE TABLE IF NOT EXISTS public.components (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  catalog_id uuid NOT NULL REFERENCES public.component_catalogs(id) ON DELETE CASCADE,
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  component_id text NOT NULL CHECK (component_id ~ '^[a-z0-9][a-z0-9._:-]{2,127}$'),
  component_set_id text,
  canonical_name text NOT NULL CHECK (btrim(canonical_name) <> ''),
  kind text NOT NULL CHECK (kind IN ('card','tile','token','die','board','figure','sheet','role','marker','track','other')),
  quantity integer CHECK (quantity IS NULL OR quantity >= 1),
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (verification_status IN ('unknown','source_bound','verified','rejected')),
  source_ids text[] NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rule_set_id, component_id),
  CHECK (verification_status NOT IN ('source_bound','verified') OR cardinality(source_ids) > 0),
  CONSTRAINT components_set_fkey
    FOREIGN KEY (rule_set_id, component_set_id)
    REFERENCES public.component_sets(rule_set_id, component_set_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.component_properties (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  component_id text NOT NULL,
  property_key text NOT NULL,
  value_type text NOT NULL,
  cardinality text NOT NULL,
  ordinal integer NOT NULL DEFAULT 0 CHECK (ordinal >= 0),
  text_value text,
  integer_value bigint,
  number_value double precision,
  boolean_value boolean,
  enum_value text,
  concept_ref_id text REFERENCES public.concepts(concept_id) ON DELETE RESTRICT,
  component_ref_id text,
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (verification_status IN ('unknown','source_bound','verified','rejected')),
  source_ids text[] NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rule_set_id, component_id, property_key, ordinal),
  CONSTRAINT component_properties_component_fkey
    FOREIGN KEY (rule_set_id, component_id)
    REFERENCES public.components(rule_set_id, component_id)
    ON DELETE CASCADE,
  CONSTRAINT component_properties_definition_fkey
    FOREIGN KEY (rule_set_id, property_key, value_type, cardinality)
    REFERENCES public.component_property_definitions(rule_set_id, property_key, value_type, cardinality)
    ON DELETE RESTRICT,
  CONSTRAINT component_properties_component_ref_fkey
    FOREIGN KEY (rule_set_id, component_ref_id)
    REFERENCES public.components(rule_set_id, component_id)
    ON DELETE RESTRICT,
  CHECK (num_nonnulls(text_value, integer_value, number_value, boolean_value, enum_value, concept_ref_id, component_ref_id) = 1),
  CHECK (
    (value_type = 'text' AND text_value IS NOT NULL) OR
    (value_type = 'integer' AND integer_value IS NOT NULL) OR
    (value_type = 'number' AND number_value IS NOT NULL) OR
    (value_type = 'boolean' AND boolean_value IS NOT NULL) OR
    (value_type = 'enum' AND enum_value IS NOT NULL) OR
    (value_type = 'concept_ref' AND concept_ref_id IS NOT NULL) OR
    (value_type = 'component_ref' AND component_ref_id IS NOT NULL)
  ),
  CHECK (verification_status NOT IN ('source_bound','verified') OR cardinality(source_ids) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS component_properties_cardinality_one
  ON public.component_properties (rule_set_id, component_id, property_key)
  WHERE cardinality = 'one';

CREATE TABLE IF NOT EXISTS public.component_abilities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  component_id text NOT NULL,
  ability_id text NOT NULL CHECK (ability_id ~ '^[a-z0-9][a-z0-9._:-]{2,127}$'),
  printed_text text,
  normalized_label text,
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (verification_status IN ('unknown','source_bound','verified','rejected')),
  source_ids text[] NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rule_set_id, ability_id),
  CONSTRAINT component_abilities_component_fkey
    FOREIGN KEY (rule_set_id, component_id)
    REFERENCES public.components(rule_set_id, component_id)
    ON DELETE CASCADE,
  CHECK (COALESCE(btrim(printed_text), '') <> '' OR COALESCE(btrim(normalized_label), '') <> ''),
  CHECK (verification_status NOT IN ('source_bound','verified') OR cardinality(source_ids) > 0)
);

CREATE TABLE IF NOT EXISTS public.component_concepts (
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  component_id text NOT NULL,
  concept_id text NOT NULL REFERENCES public.concepts(concept_id) ON DELETE RESTRICT,
  reference_kind text NOT NULL DEFAULT 'classifies' CHECK (reference_kind IN ('classifies','mentions','uses','produces')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (rule_set_id, component_id, concept_id, reference_kind),
  CONSTRAINT component_concepts_component_fkey
    FOREIGN KEY (rule_set_id, component_id)
    REFERENCES public.components(rule_set_id, component_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.component_rule_nodes (
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  component_id text NOT NULL,
  rule_id text NOT NULL,
  reference_kind text NOT NULL DEFAULT 'governed_by' CHECK (reference_kind IN ('governed_by','mentioned_by','effect_defined_by')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (rule_set_id, component_id, rule_id, reference_kind),
  CONSTRAINT component_rule_nodes_component_fkey
    FOREIGN KEY (rule_set_id, component_id)
    REFERENCES public.components(rule_set_id, component_id)
    ON DELETE CASCADE,
  CONSTRAINT component_rule_nodes_rule_fkey
    FOREIGN KEY (rule_set_id, rule_id)
    REFERENCES public.rule_nodes(rule_set_id, rule_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.component_ability_concepts (
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  ability_id text NOT NULL,
  concept_id text NOT NULL REFERENCES public.concepts(concept_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (rule_set_id, ability_id, concept_id),
  CONSTRAINT component_ability_concepts_ability_fkey
    FOREIGN KEY (rule_set_id, ability_id)
    REFERENCES public.component_abilities(rule_set_id, ability_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.component_ability_rule_nodes (
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  ability_id text NOT NULL,
  rule_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (rule_set_id, ability_id, rule_id),
  CONSTRAINT component_ability_rule_nodes_ability_fkey
    FOREIGN KEY (rule_set_id, ability_id)
    REFERENCES public.component_abilities(rule_set_id, ability_id)
    ON DELETE CASCADE,
  CONSTRAINT component_ability_rule_nodes_rule_fkey
    FOREIGN KEY (rule_set_id, rule_id)
    REFERENCES public.rule_nodes(rule_set_id, rule_id)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS component_sets_catalog_idx ON public.component_sets (catalog_id, component_set_id);
CREATE INDEX IF NOT EXISTS components_catalog_set_idx ON public.components (catalog_id, component_set_id, canonical_name);
CREATE INDEX IF NOT EXISTS component_properties_component_idx ON public.component_properties (rule_set_id, component_id, property_key, ordinal);
CREATE INDEX IF NOT EXISTS component_concepts_concept_idx ON public.component_concepts (concept_id, rule_set_id);
CREATE INDEX IF NOT EXISTS component_rule_nodes_rule_idx ON public.component_rule_nodes (rule_set_id, rule_id);

ALTER TABLE public.component_catalogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_property_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.components ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_abilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_rule_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_ability_concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.component_ability_rule_nodes ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE VIEW public.component_catalog_audit_summary
WITH (security_invoker = true) AS
SELECT
  (SELECT count(*) FROM public.component_catalogs) AS catalogs,
  (SELECT count(*) FROM public.component_sets) AS component_sets,
  (SELECT count(*) FROM public.components) AS components,
  (SELECT count(*) FROM public.component_property_definitions) AS property_definitions,
  (SELECT count(*) FROM public.component_properties) AS component_property_values,
  (SELECT count(*) FROM public.component_abilities) AS abilities,
  (SELECT count(*) FROM public.component_concepts) AS component_concept_links,
  (SELECT count(*) FROM public.component_rule_nodes) AS component_rule_links,
  (SELECT count(*) FROM public.component_properties WHERE verification_status = 'unknown') AS unknown_property_values;

COMMIT;
