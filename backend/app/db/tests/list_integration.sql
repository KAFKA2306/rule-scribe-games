\set ON_ERROR_STOP on

CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;

CREATE SCHEMA auth;
CREATE FUNCTION auth.uid()
RETURNS uuid LANGUAGE sql STABLE
AS $$ SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid; $$;

CREATE TABLE public.profiles (
  id uuid PRIMARY KEY,
  username text
);
CREATE TABLE public.games (
  id uuid PRIMARY KEY,
  title text NOT NULL,
  title_ja text,
  slug text
);

INSERT INTO public.profiles(id, username) VALUES
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','user-a'),
  ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','user-b');
INSERT INTO public.games(id, title, title_ja, slug) VALUES
  ('11111111-1111-4111-8111-111111111111','Game One','ゲーム1','game-one'),
  ('22222222-2222-4222-8222-222222222222','Game Two','ゲーム2','game-two');

\ir ../migrations/005_user_lists.sql

SET ROLE authenticated;
SET request.jwt.claim.sub = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';

INSERT INTO public.user_lists(id, owner_id, name)
VALUES ('aaaaaaaa-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Favorites');

INSERT INTO public.user_list_items(id, list_id, game_id, game_title_snapshot, position) VALUES
('aaaaaaaa-1000-4000-8000-000000000001','aaaaaaaa-0000-4000-8000-000000000001','11111111-1111-4111-8111-111111111111','ゲーム1',0),
('aaaaaaaa-1000-4000-8000-000000000002','aaaaaaaa-0000-4000-8000-000000000001','22222222-2222-4222-8222-222222222222','ゲーム2',1);

DO $$
BEGIN
  BEGIN
    INSERT INTO public.user_list_items(list_id, game_id, game_title_snapshot, position)
    VALUES ('aaaaaaaa-0000-4000-8000-000000000001','11111111-1111-4111-8111-111111111111','duplicate',2);
    RAISE EXCEPTION 'duplicate membership unexpectedly accepted';
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
END;
$$;

RESET ROLE;
RESET request.jwt.claim.sub;

SET ROLE authenticated;
SET request.jwt.claim.sub = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.user_lists) THEN
    RAISE EXCEPTION 'user B can read user A private list';
  END IF;
  IF EXISTS (SELECT 1 FROM public.user_list_items) THEN
    RAISE EXCEPTION 'user B can read user A private list items';
  END IF;
END;
$$;
UPDATE public.user_lists SET name='tampered' WHERE id='aaaaaaaa-0000-4000-8000-000000000001';
DELETE FROM public.user_list_items WHERE id='aaaaaaaa-1000-4000-8000-000000000001';
RESET ROLE;
RESET request.jwt.claim.sub;

DO $$
BEGIN
  IF (SELECT name FROM public.user_lists WHERE id='aaaaaaaa-0000-4000-8000-000000000001') <> 'Favorites' THEN
    RAISE EXCEPTION 'user B modified user A list';
  END IF;
  IF (SELECT count(*) FROM public.user_list_items WHERE list_id='aaaaaaaa-0000-4000-8000-000000000001') <> 2 THEN
    RAISE EXCEPTION 'user B deleted user A item';
  END IF;
END;
$$;

SET ROLE service_role;
SELECT public.reorder_owned_list_items(
  'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  'aaaaaaaa-0000-4000-8000-000000000001',
  ARRAY['aaaaaaaa-1000-4000-8000-000000000002','aaaaaaaa-1000-4000-8000-000000000001']::uuid[]
);
RESET ROLE;

DO $$
BEGIN
  IF (SELECT position FROM public.user_list_items WHERE id='aaaaaaaa-1000-4000-8000-000000000002') <> 0 THEN
    RAISE EXCEPTION 'reorder did not persist';
  END IF;
  IF (SELECT position FROM public.user_list_items WHERE id='aaaaaaaa-1000-4000-8000-000000000001') <> 1 THEN
    RAISE EXCEPTION 'reorder did not persist';
  END IF;
END;
$$;

DELETE FROM public.games WHERE id='11111111-1111-4111-8111-111111111111';
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.user_list_items
    WHERE id='aaaaaaaa-1000-4000-8000-000000000001'
      AND game_id IS NULL
      AND game_title_snapshot='ゲーム1'
  ) THEN
    RAISE EXCEPTION 'deleted game did not preserve unavailable item snapshot';
  END IF;
END;
$$;

SET ROLE anon;
DO $$
BEGIN
  BEGIN
    PERFORM * FROM public.user_lists;
    RAISE EXCEPTION 'anon unexpectedly read private lists';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    PERFORM public.reorder_owned_list_items(
      'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      'aaaaaaaa-0000-4000-8000-000000000001',
      ARRAY[]::uuid[]
    );
    RAISE EXCEPTION 'anon unexpectedly executed reorder RPC';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END;
$$;
RESET ROLE;
