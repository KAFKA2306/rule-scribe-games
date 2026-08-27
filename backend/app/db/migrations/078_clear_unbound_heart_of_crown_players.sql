BEGIN;

-- The physical Second Edition identity is verified, but the current first-party
-- physical rules/product material available to this pipeline has not yet bound
-- the player-count claim. Fail closed rather than retaining a legacy value.
UPDATE public.games
SET
  min_players = NULL,
  max_players = NULL,
  updated_at = now()
WHERE slug = 'heart-of-crown-2nd-edition';

COMMIT;
