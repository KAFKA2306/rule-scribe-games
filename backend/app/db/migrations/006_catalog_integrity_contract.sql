BEGIN;

-- These columns were added directly to production during the 2026-08-14
-- YRO verification. Keep the repository schema replayable from scratch.
ALTER TABLE public.games
  ADD COLUMN IF NOT EXISTS setup_summary text,
  ADD COLUMN IF NOT EXISTS gameplay_summary text,
  ADD COLUMN IF NOT EXISTS end_game_summary text;

-- Existing legacy data currently contains one null slug. NOT VALID keeps that
-- historical row reviewable while immediately rejecting new/updated null or
-- blank slugs. After the legacy row is reconciled, this constraint can be
-- VALIDATEd without changing the write contract.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'games_slug_required'
      AND conrelid = 'public.games'::regclass
  ) THEN
    ALTER TABLE public.games
      ADD CONSTRAINT games_slug_required
      CHECK (slug IS NOT NULL AND btrim(slug) <> '') NOT VALID;
  END IF;
END;
$$;

COMMIT;
