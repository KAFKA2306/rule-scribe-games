BEGIN;

-- The legacy public Game row currently renders Board Game Arena-specific rules.
-- Keep work identity bound to the publisher, but bind the displayed rule body to
-- the authorized platform source instead of presenting it as publisher rules.
UPDATE public.games
SET
  identity_source = 'https://atmgaming.com/product/pili-pili',
  source_url = 'https://ja.boardgamearena.com/gamepanel?game=pilipili',
  source_trust = 'authorized_partner'
WHERE slug = 'pili-pili'
  AND identity_status = 'verified'
  AND rules_content ILIKE '%Board Game Arena%';

COMMIT;
