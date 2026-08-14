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

-- Promote only explicit provenance already recorded in source_documents. A URL
-- or legacy is_official flag alone is never enough to establish source trust.
UPDATE public.games
SET source_trust = 'official_publisher'
WHERE slug IS NOT NULL
  AND btrim(slug) <> ''
  AND EXISTS (
    SELECT 1
    FROM jsonb_array_elements(coalesce(structured_data->'source_documents', '[]'::jsonb)) AS doc
    WHERE doc->>'type' IN ('publisher_official', 'publisher_official_faq')
  );

UPDATE public.games
SET source_trust = 'third_party'
WHERE slug IS NOT NULL
  AND btrim(slug) <> ''
  AND source_trust = 'unknown'
  AND EXISTS (
    SELECT 1
    FROM jsonb_array_elements(coalesce(structured_data->'source_documents', '[]'::jsonb)) AS doc
    WHERE doc->>'type' IN (
      'platform_official_rules',
      'platform_official_game',
      'platform_official_game_page',
      'platform_rules_summary',
      'user_supplied_replay_log'
    )
  );

-- Preserve legacy links as unclassified sources. The legacy columns remain only
-- during the compatible rollout and are removed by migration 008 after the new
-- application code is live. Skip invalid legacy slug rows so migration 006's
-- NOT VALID constraint does not reject an unrelated compatibility update.
UPDATE public.games
SET source_url = official_url
WHERE slug IS NOT NULL
  AND btrim(slug) <> ''
  AND source_url IS NULL
  AND official_url IS NOT NULL
  AND btrim(official_url) <> '';

COMMIT;
