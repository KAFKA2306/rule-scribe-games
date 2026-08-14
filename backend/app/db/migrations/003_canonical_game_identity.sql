BEGIN;

CREATE OR REPLACE FUNCTION public.normalize_game_title(value text)
RETURNS text
LANGUAGE sql
IMMUTABLE
RETURNS NULL ON NULL INPUT
AS $$
  SELECT lower(regexp_replace(trim(value), '[[:space:][:punct:]！!？?・：:]+', '', 'g'));
$$;

CREATE TABLE IF NOT EXISTS public.game_works (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_title text NOT NULL,
  bgg_id bigint,
  identity_status text NOT NULL DEFAULT 'unverified'
    CHECK (identity_status IN ('unverified', 'verified', 'needs_review')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS game_works_bgg_id_unique
  ON public.game_works (bgg_id)
  WHERE bgg_id IS NOT NULL;

ALTER TABLE public.games
  ADD COLUMN IF NOT EXISTS work_id uuid,
  ADD COLUMN IF NOT EXISTS edition_label text,
  ADD COLUMN IF NOT EXISTS language_code text,
  ADD COLUMN IF NOT EXISTS publisher text,
  ADD COLUMN IF NOT EXISTS bgg_version_id bigint,
  ADD COLUMN IF NOT EXISTS source_revision text,
  ADD COLUMN IF NOT EXISTS generated_from_source_revision text,
  ADD COLUMN IF NOT EXISTS identity_status text NOT NULL DEFAULT 'unverified';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'games_identity_status_check'
      AND conrelid = 'public.games'::regclass
  ) THEN
    ALTER TABLE public.games
      ADD CONSTRAINT games_identity_status_check
      CHECK (identity_status IN ('unverified', 'verified', 'needs_review'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'games_work_id_fkey'
      AND conrelid = 'public.games'::regclass
  ) THEN
    ALTER TABLE public.games
      ADD CONSTRAINT games_work_id_fkey
      FOREIGN KEY (work_id) REFERENCES public.game_works(id) ON DELETE RESTRICT;
  END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS games_bgg_version_id_unique
  ON public.games (bgg_version_id)
  WHERE bgg_version_id IS NOT NULL;

-- Safe bootstrap: every legacy row starts as a distinct work. We never infer a
-- merge from title/slug similarity. A BGG boardgame ID is backfilled only when
-- it is explicitly present in an existing canonical BGG URL.
INSERT INTO public.game_works (id, canonical_title, bgg_id, identity_status, created_at, updated_at)
SELECT
  g.id,
  g.title,
  CASE
    WHEN g.bgg_url ~* 'boardgame/[0-9]+'
      THEN substring(g.bgg_url from 'boardgame/([0-9]+)')::bigint
    ELSE NULL
  END,
  'unverified',
  COALESCE(g.created_at, now()),
  COALESCE(g.updated_at, now())
FROM public.games g
ON CONFLICT (id) DO NOTHING;

UPDATE public.games
SET work_id = id
WHERE work_id IS NULL;

ALTER TABLE public.games ALTER COLUMN work_id SET NOT NULL;

CREATE TABLE IF NOT EXISTS public.game_title_aliases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id uuid NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  title text NOT NULL,
  language_code text,
  normalized_title text NOT NULL,
  source text NOT NULL DEFAULT 'legacy',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS game_title_aliases_unique
  ON public.game_title_aliases (game_id, title, COALESCE(language_code, ''));
CREATE INDEX IF NOT EXISTS game_title_aliases_normalized_idx
  ON public.game_title_aliases (normalized_title);

INSERT INTO public.game_title_aliases (game_id, title, language_code, normalized_title, source)
SELECT id, title, NULL, public.normalize_game_title(title), 'games.title'
FROM public.games
WHERE title IS NOT NULL AND trim(title) <> ''
ON CONFLICT DO NOTHING;

INSERT INTO public.game_title_aliases (game_id, title, language_code, normalized_title, source)
SELECT id, title_ja, 'ja', public.normalize_game_title(title_ja), 'games.title_ja'
FROM public.games
WHERE title_ja IS NOT NULL AND trim(title_ja) <> ''
ON CONFLICT DO NOTHING;

INSERT INTO public.game_title_aliases (game_id, title, language_code, normalized_title, source)
SELECT id, title_en, 'en', public.normalize_game_title(title_en), 'games.title_en'
FROM public.games
WHERE title_en IS NOT NULL AND trim(title_en) <> ''
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS public.game_slug_aliases (
  alias_slug text PRIMARY KEY,
  game_id uuid NOT NULL REFERENCES public.games(id) ON DELETE CASCADE,
  reason text NOT NULL DEFAULT 'slug_changed',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.protect_and_capture_game_slug()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.slug IS NOT NULL AND EXISTS (
    SELECT 1
    FROM public.game_slug_aliases a
    WHERE a.alias_slug = NEW.slug
      AND a.game_id <> NEW.id
  ) THEN
    RAISE EXCEPTION 'slug % is reserved by an existing alias', NEW.slug
      USING ERRCODE = 'unique_violation';
  END IF;

  IF TG_OP = 'UPDATE'
     AND OLD.slug IS DISTINCT FROM NEW.slug
     AND OLD.slug IS NOT NULL
     AND trim(OLD.slug) <> '' THEN
    INSERT INTO public.game_slug_aliases (alias_slug, game_id, reason)
    VALUES (OLD.slug, OLD.id, 'slug_changed')
    ON CONFLICT (alias_slug) DO NOTHING;
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS capture_game_slug_alias ON public.games;
CREATE TRIGGER capture_game_slug_alias
BEFORE INSERT OR UPDATE OF slug ON public.games
FOR EACH ROW
EXECUTE FUNCTION public.protect_and_capture_game_slug();

CREATE OR REPLACE VIEW public.game_identity_duplicate_candidates AS
SELECT
  a.normalized_title,
  count(DISTINCT a.game_id) AS game_count,
  array_agg(DISTINCT a.game_id ORDER BY a.game_id) AS game_ids
FROM public.game_title_aliases a
WHERE a.normalized_title <> ''
GROUP BY a.normalized_title
HAVING count(DISTINCT a.game_id) > 1;

CREATE OR REPLACE VIEW public.game_generation_freshness AS
SELECT
  id AS game_id,
  source_url,
  source_revision,
  generated_from_source_revision,
  CASE
    WHEN source_revision IS NULL THEN 'source_revision_unknown'
    WHEN generated_from_source_revision IS NULL THEN 'generation_revision_unknown'
    WHEN source_revision = generated_from_source_revision THEN 'current'
    ELSE 'stale'
  END AS generation_status
FROM public.games;

CREATE OR REPLACE VIEW public.game_identity_audit_summary AS
SELECT
  (SELECT count(*) FROM public.games) AS total_games,
  (SELECT count(*) FROM public.game_works) AS total_works,
  (SELECT count(*) FROM public.game_works WHERE bgg_id IS NOT NULL) AS works_with_bgg_id,
  (SELECT count(*) FROM public.games WHERE bgg_version_id IS NOT NULL) AS editions_with_bgg_version_id,
  (SELECT count(*) FROM public.games WHERE language_code IS NULL) AS missing_language_code,
  (SELECT count(*) FROM public.games WHERE source_revision IS NULL) AS missing_source_revision,
  (SELECT count(*) FROM public.game_identity_duplicate_candidates) AS duplicate_title_groups;

COMMIT;
