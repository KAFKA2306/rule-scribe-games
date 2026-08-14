\set ON_ERROR_STOP on

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
END;
$$;

CREATE TABLE public.games (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  title_ja text,
  title_en text,
  slug text UNIQUE,
  bgg_url text,
  source_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO public.games (id,title,title_ja,title_en,slug,bgg_url) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Twin Game','ツインゲーム','Twin Game','twin-a','https://boardgamegeek.com/boardgame/100/twin-game-a'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','Twin Game','ツインゲーム別版','Twin Game','twin-b','https://boardgamegeek.com/boardgame/200/twin-game-b'),
('cccccccc-cccc-4ccc-8ccc-cccccccccccc','Other Game','別ゲーム','Other Game','other',NULL);

\ir ../migrations/003_canonical_game_identity.sql
\ir ../migrations/004_lock_identity_metadata.sql

DO $$
BEGIN
  IF (SELECT count(*) FROM public.games) <> 3 THEN
    RAISE EXCEPTION 'migration changed game row count';
  END IF;
  IF (SELECT count(*) FROM public.game_works) <> 3 THEN
    RAISE EXCEPTION 'title similarity caused an inferred work merge';
  END IF;
  IF EXISTS (SELECT 1 FROM public.games WHERE work_id <> id) THEN
    RAISE EXCEPTION 'legacy bootstrap must preserve one distinct work per game';
  END IF;
  IF (SELECT bgg_id FROM public.game_works WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa') <> 100 THEN
    RAISE EXCEPTION 'explicit BGG ID was not extracted';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.game_identity_duplicate_candidates
    WHERE normalized_title = public.normalize_game_title('Twin Game')
  ) THEN
    RAISE EXCEPTION 'same-title duplicate candidate was not surfaced';
  END IF;
END;
$$;

UPDATE public.games
SET language_code='en', edition_label='First edition', bgg_version_id=1001,
    source_revision='rev-2', generated_from_source_revision='rev-1'
WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';

DO $$
BEGIN
  IF (SELECT generation_status FROM public.game_generation_freshness WHERE game_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa') <> 'stale' THEN
    RAISE EXCEPTION 'source revision mismatch was not marked stale';
  END IF;
END;
$$;

UPDATE public.games SET slug='twin-a-v2'
WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.game_slug_aliases
    WHERE alias_slug='twin-a' AND game_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  ) THEN
    RAISE EXCEPTION 'old slug was not preserved as an alias';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.game_title_aliases
    WHERE game_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa' AND language_code='ja'
  ) THEN
    RAISE EXCEPTION 'localized title alias missing';
  END IF;
END;
$$;

SET ROLE anon;
DO $$
BEGIN
  BEGIN
    PERFORM * FROM public.game_works LIMIT 1;
    RAISE EXCEPTION 'anon unexpectedly read identity metadata';
  EXCEPTION WHEN insufficient_privilege THEN
    NULL;
  END;
END;
$$;
RESET ROLE;
