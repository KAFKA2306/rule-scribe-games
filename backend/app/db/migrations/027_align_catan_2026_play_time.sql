BEGIN;

-- Align the production metadata with the GP Games Japanese 2026 renewed
-- Standard Edition. Do not reuse this value for older Japanese editions.
DO $$
DECLARE
  v_updated integer;
BEGIN
  UPDATE public.games
  SET
    play_time = 60,
    updated_at = now()
  WHERE slug = 'catan'
    AND identity_status = 'verified'
    AND identity_source = 'https://www.gp-inc.jp/boardgame_catan_new_s.html'
    AND edition_label = 'GP Games 日本語版 スタンダード版 (2026リニューアル)';

  GET DIAGNOSTICS v_updated = ROW_COUNT;
  IF v_updated <> 1 THEN
    RAISE EXCEPTION 'Expected exactly one verified GP Games 2026 Catan row, updated %', v_updated;
  END IF;
END $$;

COMMIT;
