-- Keep catalog storage aligned with the GameDetail / curated-game identity provenance contract.
-- Existing rows remain NULL until their identity evidence is reviewed; do not infer provenance.

BEGIN;

ALTER TABLE public.games
  ADD COLUMN IF NOT EXISTS identity_source text;

COMMIT;
