BEGIN;

ALTER TABLE public.game_works ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_title_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_slug_aliases ENABLE ROW LEVEL SECURITY;

REVOKE ALL PRIVILEGES ON TABLE public.game_works FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.game_title_aliases FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.game_slug_aliases FROM anon, authenticated;

REVOKE ALL PRIVILEGES ON TABLE public.game_identity_duplicate_candidates FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.game_generation_freshness FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.game_identity_audit_summary FROM anon, authenticated;

COMMIT;
