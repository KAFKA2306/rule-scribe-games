BEGIN;

ALTER TABLE public.rule_sets
  ADD COLUMN IF NOT EXISTS revision_label text,
  ADD COLUMN IF NOT EXISTS platform text,
  ADD COLUMN IF NOT EXISTS publisher_name text,
  ADD COLUMN IF NOT EXISTS publication_date date,
  ADD COLUMN IF NOT EXISTS effective_date date,
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'unknown',
  ADD COLUMN IF NOT EXISTS verification_status text NOT NULL DEFAULT 'unknown',
  ADD COLUMN IF NOT EXISTS base_rule_set_id uuid REFERENCES public.rule_sets(id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS relation_type text,
  ADD COLUMN IF NOT EXISTS variant_label text,
  ADD COLUMN IF NOT EXISTS source_ids text[] NOT NULL DEFAULT '{}';

ALTER TABLE public.rule_sets
  DROP CONSTRAINT IF EXISTS rule_sets_game_id_version_key;

DROP INDEX IF EXISTS public.rule_sets_one_active_per_game;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'rule_sets_status_check'
      AND conrelid = 'public.rule_sets'::regclass
  ) THEN
    ALTER TABLE public.rule_sets
      ADD CONSTRAINT rule_sets_status_check
      CHECK (status IN ('unknown', 'active', 'superseded'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'rule_sets_verification_status_check'
      AND conrelid = 'public.rule_sets'::regclass
  ) THEN
    ALTER TABLE public.rule_sets
      ADD CONSTRAINT rule_sets_verification_status_check
      CHECK (verification_status IN ('unknown', 'source_bound', 'verified', 'rejected'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'rule_sets_relation_type_check'
      AND conrelid = 'public.rule_sets'::regclass
  ) THEN
    ALTER TABLE public.rule_sets
      ADD CONSTRAINT rule_sets_relation_type_check
      CHECK (relation_type IS NULL OR relation_type IN ('derived_from', 'variant_of', 'translation_of', 'supersedes'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'rule_sets_relation_pair_check'
      AND conrelid = 'public.rule_sets'::regclass
  ) THEN
    ALTER TABLE public.rule_sets
      ADD CONSTRAINT rule_sets_relation_pair_check
      CHECK ((base_rule_set_id IS NULL) = (relation_type IS NULL));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'rule_sets_no_self_parent_check'
      AND conrelid = 'public.rule_sets'::regclass
  ) THEN
    ALTER TABLE public.rule_sets
      ADD CONSTRAINT rule_sets_no_self_parent_check
      CHECK (base_rule_set_id IS NULL OR base_rule_set_id <> id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'rule_sets_variant_label_check'
      AND conrelid = 'public.rule_sets'::regclass
  ) THEN
    ALTER TABLE public.rule_sets
      ADD CONSTRAINT rule_sets_variant_label_check
      CHECK (relation_type <> 'variant_of' OR (variant_label IS NOT NULL AND btrim(variant_label) <> ''));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'rule_sets_status_activity_check'
      AND conrelid = 'public.rule_sets'::regclass
  ) THEN
    ALTER TABLE public.rule_sets
      ADD CONSTRAINT rule_sets_status_activity_check
      CHECK (
        (status <> 'superseded' OR NOT is_active)
        AND (status <> 'active' OR is_active)
      );
  END IF;
END $$;

-- Keep multiple simultaneously active RuleSets for one Game when their identity
-- axes differ (for example publisher physical rules vs BGA, or ja vs en).
-- Do not infer any missing edition/language/platform/revision during migration.
CREATE UNIQUE INDEX IF NOT EXISTS rule_sets_identity_version_unique
  ON public.rule_sets (
    game_id,
    COALESCE(edition_label, ''),
    COALESCE(language_code, ''),
    COALESCE(platform, ''),
    COALESCE(revision_label, ''),
    COALESCE(variant_label, ''),
    version
  );

CREATE UNIQUE INDEX IF NOT EXISTS rule_sets_one_active_per_identity
  ON public.rule_sets (
    game_id,
    COALESCE(edition_label, ''),
    COALESCE(language_code, ''),
    COALESCE(platform, ''),
    COALESCE(revision_label, ''),
    COALESCE(variant_label, '')
  )
  WHERE is_active;

CREATE INDEX IF NOT EXISTS rule_sets_game_active_idx
  ON public.rule_sets (game_id, is_active, version DESC);

CREATE INDEX IF NOT EXISTS rule_sets_base_relation_idx
  ON public.rule_sets (base_rule_set_id, relation_type)
  WHERE base_rule_set_id IS NOT NULL;

COMMIT;
