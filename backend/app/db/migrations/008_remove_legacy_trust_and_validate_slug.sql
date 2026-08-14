BEGIN;

-- Apply only after application code has switched to source_url/source_trust and
-- after the audited production null-slug row has been reconciled.
ALTER TABLE public.games DROP COLUMN IF EXISTS is_official;
ALTER TABLE public.games DROP COLUMN IF EXISTS official_url;

ALTER TABLE public.games DROP CONSTRAINT IF EXISTS games_slug_required;
ALTER TABLE public.games
  ADD CONSTRAINT games_slug_required
  CHECK (slug IS NOT NULL AND btrim(slug) <> '');

COMMIT;
