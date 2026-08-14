BEGIN;

CREATE TABLE IF NOT EXISTS public.concepts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id text NOT NULL UNIQUE CHECK (concept_id ~ '^[a-z0-9][a-z0-9._:-]{2,127}$'),
  concept_type text NOT NULL CHECK (
    concept_type IN (
      'mechanic', 'component', 'resource', 'state', 'player_action',
      'information_structure', 'interaction_pattern', 'rule_pattern'
    )
  ),
  lifecycle_status text NOT NULL DEFAULT 'active' CHECK (
    lifecycle_status IN ('active', 'deprecated', 'merged')
  ),
  replaced_by_concept_id text REFERENCES public.concepts(concept_id) ON DELETE RESTRICT,
  definition text,
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (
    verification_status IN ('unknown', 'source_bound', 'verified')
  ),
  source_url text,
  source_locator text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (replaced_by_concept_id IS NULL OR replaced_by_concept_id <> concept_id),
  CHECK (
    (lifecycle_status = 'merged' AND replaced_by_concept_id IS NOT NULL)
    OR (lifecycle_status <> 'merged' AND replaced_by_concept_id IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS public.concept_labels (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id text NOT NULL REFERENCES public.concepts(concept_id) ON DELETE CASCADE,
  language_code text NOT NULL CHECK (length(trim(language_code)) >= 2),
  label_type text NOT NULL CHECK (label_type IN ('pref', 'alt')),
  label text NOT NULL CHECK (trim(label) <> ''),
  normalized_label text NOT NULL CHECK (trim(normalized_label) <> ''),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS concept_labels_unique_normalized_per_language
  ON public.concept_labels (concept_id, lower(language_code), normalized_label);
CREATE UNIQUE INDEX IF NOT EXISTS concept_labels_one_pref_per_language
  ON public.concept_labels (concept_id, lower(language_code))
  WHERE label_type = 'pref';
CREATE INDEX IF NOT EXISTS concept_labels_lookup_idx
  ON public.concept_labels (lower(language_code), normalized_label);

CREATE TABLE IF NOT EXISTS public.concept_relations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_concept_id text NOT NULL REFERENCES public.concepts(concept_id) ON DELETE CASCADE,
  to_concept_id text NOT NULL REFERENCES public.concepts(concept_id) ON DELETE CASCADE,
  relation_type text NOT NULL CHECK (
    relation_type IN ('broader', 'narrower', 'related', 'replaced_by')
  ),
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (
    verification_status IN ('unknown', 'source_bound', 'verified')
  ),
  source_url text,
  source_locator text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (from_concept_id, to_concept_id, relation_type),
  CHECK (from_concept_id <> to_concept_id)
);

CREATE INDEX IF NOT EXISTS concept_relations_from_idx
  ON public.concept_relations (from_concept_id, relation_type);
CREATE INDEX IF NOT EXISTS concept_relations_to_idx
  ON public.concept_relations (to_concept_id, relation_type);

CREATE TABLE IF NOT EXISTS public.game_concepts (
  game_id uuid NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  concept_id text NOT NULL REFERENCES public.concepts(concept_id) ON DELETE RESTRICT,
  usage_role text NOT NULL CHECK (usage_role IN ('core', 'supporting', 'glossary')),
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (
    verification_status IN ('unknown', 'source_bound', 'verified')
  ),
  source_url text,
  source_locator text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (game_id, concept_id, usage_role)
);

CREATE TABLE IF NOT EXISTS public.rule_node_concepts (
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  rule_id text NOT NULL,
  concept_id text NOT NULL REFERENCES public.concepts(concept_id) ON DELETE RESTRICT,
  reference_kind text NOT NULL CHECK (
    reference_kind IN ('mentions', 'defines', 'requires', 'modifies')
  ),
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (
    verification_status IN ('unknown', 'source_bound', 'verified')
  ),
  source_url text,
  source_locator text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (rule_set_id, rule_id, concept_id, reference_kind),
  CONSTRAINT rule_node_concepts_rule_fkey
    FOREIGN KEY (rule_set_id, rule_id)
    REFERENCES public.rule_nodes(rule_set_id, rule_id)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS rule_node_concepts_concept_idx
  ON public.rule_node_concepts (concept_id, rule_set_id);

ALTER TABLE public.concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.concept_labels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.concept_relations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rule_node_concepts ENABLE ROW LEVEL SECURITY;

-- #149 introduced this audit view before production DDL linting was wired into the rollout.
-- Preserve the view while making it obey the querying role's permissions/RLS.
ALTER VIEW IF EXISTS public.rule_graph_audit_summary SET (security_invoker = true);

CREATE OR REPLACE VIEW public.concept_taxonomy_audit_summary
WITH (security_invoker = true) AS
SELECT
  (SELECT count(*) FROM public.concepts) AS concepts,
  (SELECT count(*) FROM public.concept_labels WHERE label_type = 'pref') AS preferred_labels,
  (SELECT count(*) FROM public.concept_labels WHERE label_type = 'alt') AS alternate_labels,
  (SELECT count(*) FROM public.concept_relations) AS relations,
  (SELECT count(DISTINCT game_id) FROM public.game_concepts) AS games_with_concepts,
  (SELECT count(*) FROM public.rule_node_concepts) AS rule_concept_links,
  (SELECT count(*) FROM public.concepts WHERE verification_status <> 'verified') AS unresolved_concepts;

COMMIT;
