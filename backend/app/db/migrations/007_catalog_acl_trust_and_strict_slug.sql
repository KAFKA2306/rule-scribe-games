BEGIN;

CREATE TABLE IF NOT EXISTS public.catalog_editors (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('owner', 'editor')),
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.catalog_editors
  ADD COLUMN IF NOT EXISTS active boolean NOT NULL DEFAULT true;
ALTER TABLE public.catalog_editors ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS public.catalog_mutation_audit (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
  game_slug text NOT NULL,
  action text NOT NULL CHECK (action IN ('manual_update', 'regenerate')),
  changed_fields text[] NOT NULL DEFAULT '{}',
  outcome text NOT NULL CHECK (outcome IN ('allowed', 'denied', 'succeeded', 'not_found', 'failed')),
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.catalog_mutation_audit ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS catalog_mutation_audit_created_at_idx
  ON public.catalog_mutation_audit (created_at DESC);
CREATE INDEX IF NOT EXISTS catalog_mutation_audit_game_slug_idx
  ON public.catalog_mutation_audit (game_slug);

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

UPDATE public.games
SET source_url = official_url
WHERE slug IS NOT NULL
  AND btrim(slug) <> ''
  AND source_url IS NULL
  AND official_url IS NOT NULL
  AND btrim(official_url) <> '';

COMMIT;
