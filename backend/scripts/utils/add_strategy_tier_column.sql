-- Add strategy_tier column to games table
ALTER TABLE games ADD COLUMN IF NOT EXISTS strategy_tier TEXT;

-- Index for querying by tier
CREATE INDEX IF NOT EXISTS idx_games_strategy_tier ON games(strategy_tier);
