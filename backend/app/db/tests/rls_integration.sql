\set ON_ERROR_STOP on

CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;

CREATE SCHEMA auth;
CREATE FUNCTION auth.uid()
RETURNS uuid
LANGUAGE sql
STABLE
AS $$
  SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$;

CREATE TABLE public.profiles (
  id uuid PRIMARY KEY,
  username text UNIQUE,
  avatar_url text,
  updated_at timestamptz
);

CREATE TABLE public.games (
  id uuid PRIMARY KEY
);

CREATE TABLE public.user_games (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  game_id uuid NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  status text NOT NULL,
  rating integer,
  comment text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE (user_id, game_id)
);

INSERT INTO public.profiles (id, username) VALUES
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'user-a'),
  ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', 'user-b');
INSERT INTO public.games (id) VALUES
  ('11111111-1111-4111-8111-111111111111'),
  ('22222222-2222-4222-8222-222222222222');

\ir ../migrations/002_harden_user_data_rls.sql

SET ROLE authenticated;
SET request.jwt.claim.sub = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';

INSERT INTO public.user_games (id, user_id, game_id, status, comment)
VALUES (
  'aaaaaaaa-0000-4000-8000-000000000001',
  'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '11111111-1111-4111-8111-111111111111',
  'owned',
  'created-by-a'
);

DO $$
BEGIN
  IF (SELECT count(*) FROM public.user_games) <> 1 THEN
    RAISE EXCEPTION 'user A cannot read its own row';
  END IF;
END;
$$;

UPDATE public.user_games
SET comment = 'updated-by-a'
WHERE id = 'aaaaaaaa-0000-4000-8000-000000000001';

INSERT INTO public.user_games (id, user_id, game_id, status)
VALUES (
  'aaaaaaaa-0000-4000-8000-000000000002',
  'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '22222222-2222-4222-8222-222222222222',
  'wishlist'
);
DELETE FROM public.user_games
WHERE id = 'aaaaaaaa-0000-4000-8000-000000000002';

RESET ROLE;
RESET request.jwt.claim.sub;

SET ROLE authenticated;
SET request.jwt.claim.sub = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.user_games) THEN
    RAISE EXCEPTION 'user B can read user A private row';
  END IF;
END;
$$;

UPDATE public.user_games
SET comment = 'tampered-by-b'
WHERE id = 'aaaaaaaa-0000-4000-8000-000000000001';
DELETE FROM public.user_games
WHERE id = 'aaaaaaaa-0000-4000-8000-000000000001';

RESET ROLE;
RESET request.jwt.claim.sub;

DO $$
DECLARE
  v_comment text;
BEGIN
  SELECT comment INTO v_comment
  FROM public.user_games
  WHERE id = 'aaaaaaaa-0000-4000-8000-000000000001';

  IF v_comment IS DISTINCT FROM 'updated-by-a' THEN
    RAISE EXCEPTION 'user B modified user A row: %', v_comment;
  END IF;
END;
$$;
