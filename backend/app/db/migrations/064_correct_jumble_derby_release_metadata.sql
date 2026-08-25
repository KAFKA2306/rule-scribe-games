BEGIN;

-- Align residual catalog metadata with the creator's 2023秋 release identity.
-- No authoritative BoardGameGeek record was verified during the source audit, so do not retain the stale imported link as canonical metadata.
UPDATE public.games
SET published_year=2023,
    bgg_url=NULL,
    updated_at=now()
WHERE slug='jumble-derby'
  AND identity_status='verified'
  AND identity_source='https://gamemarket.jp/game/181906';

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.games
    WHERE slug='jumble-derby'
      AND (published_year IS DISTINCT FROM 2023 OR bgg_url IS NOT NULL)
  ) THEN
    RAISE EXCEPTION 'Jumble Derby release metadata must be 2023 with no unverified BGG URL';
  END IF;
END $$;

COMMIT;
