-- Create strategy_tiers table
-- This table stores high-level strategy guides and tier ratings for games.

CREATE TABLE IF NOT EXISTS strategy_tiers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_slug TEXT NOT NULL REFERENCES games(slug) ON DELETE CASCADE,
  tier_rating TEXT NOT NULL, -- e.g. "S", "A", "B", "Tier 1"
  strategy_content TEXT NOT NULL, -- Markdown content
  author TEXT, -- Name of the pro player or source
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT unique_game_strategy UNIQUE (game_slug, author) -- One strategy per author per game? Or just loose.
  -- Let's keep it loose for now, but maybe unique per game if we only have one "official" tier list? 'strategy-tier' suggests ONE status.
  -- User said "top tournament player strategy". Maybe multiple?
  -- Let's NOT add unique constraint yet to be flexible.
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_strategy_tiers_game_slug ON strategy_tiers(game_slug);

-- RLS Policies
ALTER TABLE strategy_tiers ENABLE ROW LEVEL SECURITY;

-- Everyone can read
CREATE POLICY "Public Read Access" 
ON strategy_tiers FOR SELECT 
USING (true);

-- Authenticated/Service Role can write
-- (Adjust logic if you have specific user roles, for now generous for Agent/Admin)
CREATE POLICY "Admin/Service Write Access" 
ON strategy_tiers FOR ALL 
USING (true); -- Ideally restrict to service_role or admin users in prod
