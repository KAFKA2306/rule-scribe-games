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

-- A/B: same title but verified distinct BGG work IDs.
-- C/D: same work represented by separate English/Japanese editions; D starts
-- unlinked and is linked only after explicit verification in the fixture.
INSERT INTO public.games (id,title,title_ja,title_en,slug,bgg_url) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Twin Game','ツインゲーム','Twin Game','twin-a','https://boardgamegeek.com/boardgame/100/twin-game-a'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','Twin Game','ツインゲーム別作品','Twin Game','twin-b','https://boardgamegeek.com/boardgame/200/twin-game-b'),
('cccccccc-cccc-4ccc-8ccc-cccccccccccc','Shared Work','共有ゲーム','Shared Work','shared-en','https://boardgamegeek.com/boardgame/300/shared-work'),
('dddddddd-dddd-4ddd-8ddd-dddddddddddd','共有ゲーム 日本語版','共有ゲーム 日本語版','Shared Work Japanese Edition','shared-ja',NULL);

\ir ../migrations/003_canonical_game_identity.sql
\ir ../migrations/004_lock_identity_metadata.sql

DO $$
BEGIN
  IF (SELECT count(*) FROM public.games) <> 4 THEN
    RAISE EXCEPTION 'migration changed game row count';
  END IF;
  IF (SELECT count(*) FROM public.game_works) <> 4 THEN
    RAISE EXCEPTION 'migration inferred a work merge';
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
    RAISE EXCEPTION 'same-title distinct-work candidate was not surfaced';
  END IF;
END;
$$;

-- Simulate verified same-work evidence. The two editions remain distinct rows and
-- receive distinct BGG version IDs and language codes.
UPDATE public.games
SET language_code='en', edition_label='English edition', bgg_version_id=3001
WHERE id='cccccccc-cccc-4ccc-8ccc-cccccccccccc';

UPDATE public.games
SET work_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    language_code='ja', edition_label='Japanese edition', bgg_version_id=3002
WHERE id='dddddddd-dddd-4ddd-8ddd-dddddddddddd';

DO $$
BEGIN
  IF (SELECT work_id FROM public.games WHERE id='cccccccc-cccc-4ccc-8ccc-cccccccccccc')
     IS DISTINCT FROM
     (SELECT work_id FROM public.games WHERE id='dddddddd-dddd-4ddd-8ddd-dddddddddddd') THEN
    RAISE EXCEPTION 'verified EN/JA editions do not share work identity';
  END IF;
  IF (SELECT bgg_version_id FROM public.games WHERE id='cccccccc-cccc-4ccc-8ccc-cccccccccccc') =
     (SELECT bgg_version_id FROM public.games WHERE id='dddddddd-dddd-4ddd-8ddd-dddddddddddd') THEN
    RAISE EXCEPTION 'separate editions collapsed to one edition identity';
  END IF;
END;
$$;

UPDATE public.games
SET source_revision='rev-2', generated_from_source_revision='rev-1'
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
    WHERE game_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc' AND language_code='ja'
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
