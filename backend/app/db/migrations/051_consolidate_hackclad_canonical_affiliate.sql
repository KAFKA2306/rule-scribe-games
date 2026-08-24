-- Preserve monetization when retiring the legacy `hackclad` duplicate.
-- The verified canonical work is `hack-clad`; copy the existing affiliate URL only
-- when the canonical record does not already have one.
UPDATE games AS canonical
SET amazon_url = legacy.amazon_url,
    updated_at = NOW()
FROM games AS legacy
WHERE canonical.slug = 'hack-clad'
  AND legacy.slug = 'hackclad'
  AND canonical.amazon_url IS NULL
  AND legacy.amazon_url IS NOT NULL;
