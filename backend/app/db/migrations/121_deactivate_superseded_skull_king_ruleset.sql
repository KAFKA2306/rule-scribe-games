BEGIN;

-- Skull King の現行英語版・通常ルールでは active RuleSet を1件だけにする。
-- 旧監査時点の RuleSet は履歴として残し、公開投影の authority からのみ外す。
DO $$
DECLARE
  v_game_id uuid;
  v_current_ruleset_id uuid;
  v_active_count integer;
BEGIN
  SELECT id
    INTO v_game_id
  FROM public.games
  WHERE slug = 'skull-king'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Skull King game row is required before deactivating superseded RuleSets';
  END IF;

  SELECT id
    INTO v_current_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND language_code = 'en'
    AND edition_label = 'Grandpa Beck''s Games current edition'
    AND platform = 'physical'
    AND revision_label = 'current-web-rulebook-1764178570'
    AND COALESCE(variant_label, '') = ''
    AND version = 1
    AND verification_status = 'source_bound'
  LIMIT 1;

  IF v_current_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Verified current Skull King RuleSet is required before deactivating superseded RuleSets';
  END IF;

  UPDATE public.rule_sets
  SET
    is_active = false,
    status = 'superseded',
    updated_at = now()
  WHERE game_id = v_game_id
    AND id <> v_current_ruleset_id
    AND is_active
    AND language_code = 'en'
    AND edition_label = 'Grandpa Beck''s Games current edition'
    AND platform = 'physical'
    AND COALESCE(variant_label, '') = '';

  UPDATE public.rule_sets
  SET
    is_active = true,
    status = 'active',
    updated_at = now()
  WHERE id = v_current_ruleset_id;

  SELECT count(*)
    INTO v_active_count
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active
    AND status = 'active'
    AND language_code = 'en'
    AND edition_label = 'Grandpa Beck''s Games current edition'
    AND platform = 'physical'
    AND COALESCE(variant_label, '') = '';

  IF v_active_count <> 1 THEN
    RAISE EXCEPTION 'Expected exactly one active Skull King current English physical base RuleSet, found %', v_active_count;
  END IF;
END $$;

COMMIT;
