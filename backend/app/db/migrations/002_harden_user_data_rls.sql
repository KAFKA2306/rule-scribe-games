BEGIN;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_games ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public profiles are viewable by everyone." ON public.profiles;
DROP POLICY IF EXISTS "Users can insert their own profile." ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile." ON public.profiles;

DROP POLICY IF EXISTS "User games are viewable by everyone." ON public.user_games;
DROP POLICY IF EXISTS "Users can delete their own game data." ON public.user_games;
DROP POLICY IF EXISTS "Users can insert their own game data." ON public.user_games;
DROP POLICY IF EXISTS "Users can update their own game data." ON public.user_games;

CREATE POLICY profiles_public_read
ON public.profiles
FOR SELECT
TO anon, authenticated
USING (true);

CREATE POLICY profiles_insert_own
ON public.profiles
FOR INSERT
TO authenticated
WITH CHECK ((SELECT auth.uid()) = id);

CREATE POLICY profiles_update_own
ON public.profiles
FOR UPDATE
TO authenticated
USING ((SELECT auth.uid()) = id)
WITH CHECK ((SELECT auth.uid()) = id);

CREATE POLICY user_games_select_own
ON public.user_games
FOR SELECT
TO authenticated
USING ((SELECT auth.uid()) = user_id);

CREATE POLICY user_games_insert_own
ON public.user_games
FOR INSERT
TO authenticated
WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY user_games_update_own
ON public.user_games
FOR UPDATE
TO authenticated
USING ((SELECT auth.uid()) = user_id)
WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY user_games_delete_own
ON public.user_games
FOR DELETE
TO authenticated
USING ((SELECT auth.uid()) = user_id);

REVOKE ALL PRIVILEGES ON TABLE public.profiles FROM anon, authenticated;
GRANT SELECT ON TABLE public.profiles TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.profiles TO authenticated;

REVOKE ALL PRIVILEGES ON TABLE public.user_games FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.user_games TO authenticated;

COMMIT;
