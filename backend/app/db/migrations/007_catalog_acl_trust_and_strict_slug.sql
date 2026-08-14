BEGIN;

-- Global catalog mutation is a privileged server-side operation. RLS is enabled
-- without browser policies so only the service-role backend can inspect/edit ACLs.
CREATE TABLE IF NOT EXISTS public.catalog_editors (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('editor', 'admin')),
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.catalog_editors ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS public.catalog_mutation_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  editor_user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  game_id uuid REFERENCES public.games(id) ON DELETE SET NULL,
  slug text NOT NULL,
  action text NOT NULL CHECK (action IN ('manual_update', 'regenerate')),
  changed_fields text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.catalog_mutation_audit ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS catalog_mutation_audit_created_at_idx
  ON public.catalog_mutation_audit (created_at DESC);
CREATE INDEX IF NOT EXISTS catalog_mutation_audit_game_id_idx
  ON public.catalog_mutation_audit (game_id);

-- Trust is deliberately split into orthogonal axes. Existing is_official values
-- are not evidence: every legacy row starts fail-closed as unknown.
ALTER TABLE public.games
  ADD COLUMN IF NOT EXISTS source_trust text NOT NULL DEFAULT 'unknown',
  ADD COLUMN IF NOT EXISTS content_review_status text NOT NULL DEFAULT 'unknown';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'games_source_trust_check'
      AND conrelid = 'public.games'::regclass
  ) THEN
    ALTER TABLE public.games
      ADD CONSTRAINT games_source_trust_check
      CHECK (source_trust IN ('unknown', 'official_publisher', 'authorized_partner', 'third_party'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'games_content_review_status_check'
      AND conrelid = 'public.games'::regclass
  ) THEN
    ALTER TABLE public.games
      ADD CONSTRAINT games_content_review_status_check
      CHECK (content_review_status IN ('unknown', 'ai_draft', 'review_required', 'human_reviewed', 'publisher_reviewed'));
  END IF;
END;
$$;

UPDATE public.games SET source_trust = 'unknown' WHERE source_trust IS DISTINCT FROM 'unknown';
UPDATE public.games SET content_review_status = 'unknown' WHERE content_review_status IS NULL OR btrim(content_review_status) = '';

-- The legacy boolean conflated source authenticity, identity and endorsement.
-- Once the explicit columns exist it must not remain a second source of truth.
ALTER TABLE public.games DROP COLUMN IF EXISTS is_official;

-- #138 production data is reconciled before this migration is applied. Fresh
-- databases have no historical exception, so the invariant is strict and valid.
ALTER TABLE public.games DROP CONSTRAINT IF EXISTS games_slug_required;
ALTER TABLE public.games
  ADD CONSTRAINT games_slug_required
  CHECK (slug IS NOT NULL AND btrim(slug) <> '');

COMMIT;
