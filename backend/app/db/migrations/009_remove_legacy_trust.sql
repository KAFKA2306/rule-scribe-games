BEGIN;

-- Apply only after the application version that reads source_url/source_trust
-- and no longer reads or writes is_official/official_url is confirmed live.
ALTER TABLE public.games DROP COLUMN IF EXISTS is_official;
ALTER TABLE public.games DROP COLUMN IF EXISTS official_url;

COMMIT;
