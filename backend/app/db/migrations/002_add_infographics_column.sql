BEGIN;

-- Add infographics column to games table
ALTER TABLE games ADD COLUMN IF NOT EXISTS infographics JSONB;

-- Create index for faster querying
CREATE INDEX IF NOT EXISTS idx_games_infographics ON games USING gin (infographics);

COMMIT;
