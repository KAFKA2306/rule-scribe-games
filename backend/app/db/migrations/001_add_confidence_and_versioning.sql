BEGIN;

-- Add confidence columns to games table
ALTER TABLE games ADD COLUMN IF NOT EXISTS rules_confidence NUMERIC DEFAULT 0.5 CHECK (rules_confidence >= 0 AND rules_confidence <= 1.0);
ALTER TABLE games ADD COLUMN IF NOT EXISTS setup_confidence NUMERIC DEFAULT 0.5 CHECK (setup_confidence >= 0 AND setup_confidence <= 1.0);
ALTER TABLE games ADD COLUMN IF NOT EXISTS gameplay_confidence NUMERIC DEFAULT 0.5 CHECK (gameplay_confidence >= 0 AND gameplay_confidence <= 1.0);
ALTER TABLE games ADD COLUMN IF NOT EXISTS end_game_confidence NUMERIC DEFAULT 0.5 CHECK (end_game_confidence >= 0 AND end_game_confidence <= 1.0);

-- Add versioning
ALTER TABLE games ADD COLUMN IF NOT EXISTS data_version INT DEFAULT 1;
ALTER TABLE games ADD COLUMN IF NOT EXISTS last_regenerated_at TIMESTAMP;

-- Create audit table for tracking changes
CREATE TABLE IF NOT EXISTS game_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    rules_summary TEXT,
    setup_summary TEXT,
    gameplay_summary TEXT,
    end_game_summary TEXT,
    metadata JSONB,
    version INT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_game_versions_game_id ON game_versions(game_id);
CREATE INDEX IF NOT EXISTS idx_game_versions_version ON game_versions(game_id, version);

COMMIT;
