BEGIN;

CREATE TABLE IF NOT EXISTS public.rule_sets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id uuid NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  work_id uuid REFERENCES public.game_works(id) ON DELETE RESTRICT,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  schema_version text NOT NULL DEFAULT '1.0',
  language_code text,
  edition_label text,
  source_revision text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (game_id, version)
);

CREATE UNIQUE INDEX IF NOT EXISTS rule_sets_one_active_per_game
  ON public.rule_sets (game_id)
  WHERE is_active;

CREATE TABLE IF NOT EXISTS public.rule_nodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  rule_id text NOT NULL,
  node_type text NOT NULL CHECK (
    node_type IN (
      'phase', 'turn', 'action', 'condition', 'effect', 'setup', 'scoring',
      'round_end', 'game_end', 'victory', 'exception', 'targeting',
      'conflict_resolution', 'variant'
    )
  ),
  normalized_statement text NOT NULL CHECK (trim(normalized_statement) <> ''),
  sequence integer CHECK (sequence IS NULL OR sequence >= 0),
  phase_rule_id text,
  verification_status text NOT NULL DEFAULT 'unknown' CHECK (
    verification_status IN ('unknown', 'unverified', 'source_bound', 'verified', 'rejected')
  ),
  source_claim_ref text,
  evidence_ref text,
  source_url text,
  source_locator text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rule_set_id, rule_id)
);

CREATE TABLE IF NOT EXISTS public.rule_edges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_set_id uuid NOT NULL REFERENCES public.rule_sets(id) ON DELETE CASCADE,
  from_rule_id text NOT NULL,
  to_rule_id text NOT NULL,
  relation_type text NOT NULL CHECK (
    relation_type IN (
      'contains', 'next', 'condition_effect', 'results_in', 'overrides',
      'targets', 'variant_of', 'requires'
    )
  ),
  sequence integer CHECK (sequence IS NULL OR sequence >= 0),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT rule_edges_from_rule_fkey
    FOREIGN KEY (rule_set_id, from_rule_id)
    REFERENCES public.rule_nodes(rule_set_id, rule_id)
    ON DELETE CASCADE,
  CONSTRAINT rule_edges_to_rule_fkey
    FOREIGN KEY (rule_set_id, to_rule_id)
    REFERENCES public.rule_nodes(rule_set_id, rule_id)
    ON DELETE CASCADE,
  CHECK (from_rule_id <> to_rule_id)
);

ALTER TABLE public.rule_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rule_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rule_edges ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS rule_nodes_type_idx
  ON public.rule_nodes (rule_set_id, node_type);
CREATE INDEX IF NOT EXISTS rule_edges_relation_idx
  ON public.rule_edges (rule_set_id, relation_type);

CREATE OR REPLACE VIEW public.rule_graph_audit_summary AS
SELECT
  count(DISTINCT rs.id) AS rule_sets,
  count(DISTINCT rn.id) AS rule_nodes,
  count(DISTINCT re.id) AS rule_edges,
  count(DISTINCT rs.game_id) AS games_with_rule_graph,
  count(DISTINCT rn.id) FILTER (WHERE rn.verification_status = 'verified') AS verified_nodes,
  count(DISTINCT rn.id) FILTER (WHERE rn.verification_status IN ('unknown', 'unverified')) AS unresolved_nodes
FROM public.rule_sets rs
LEFT JOIN public.rule_nodes rn ON rn.rule_set_id = rs.id
LEFT JOIN public.rule_edges re ON re.rule_set_id = rs.id
WHERE rs.is_active;

COMMIT;
