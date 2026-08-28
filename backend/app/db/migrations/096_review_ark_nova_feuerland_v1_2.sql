BEGIN;

-- プレイヤー向け完了条件:
-- アーク・ノヴァ 新たなる方舟 日本語版の基本ルール12件が、
-- Feuerland Spiele公式 Ark Nova Rulebook Version 1.2 にすべて結び付き、
-- 公式商品情報の1～4人・90～150分・14歳以上を保持できる場合だけ検索対象へ戻す。
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id FROM public.games WHERE slug = 'ark-nova' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE EXCEPTION 'Canonical Ark Nova game row is required'; END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'アーク・ノヴァ 新たなる方舟 日本語版'
    AND COALESCE(revision_label, '') = 'feuerland-rulebook-v1.2'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
  LIMIT 1;
  IF v_ruleset_id IS NULL THEN RAISE EXCEPTION 'Active source-bound Ark Nova Japanese RuleSet is required'; END IF;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status=('source'||'_'||'bound')) <> 12 THEN
    RAISE EXCEPTION 'Ark Nova requires exactly 12 source-bound RuleNodes';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 12 THEN
    RAISE EXCEPTION 'Ark Nova requires exactly 12 accepted rule claims';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND c.target_type='rule_node' AND c.lifecycle_status='accepted' AND eb.relation='supports') <> 12 THEN
    RAISE EXCEPTION 'Ark Nova requires exactly 12 supporting evidence bindings';
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id
    WHERE c.rule_set_id=v_ruleset_id AND c.target_type='rule_node' AND c.lifecycle_status='accepted' AND eb.relation='supports'
      AND eb.source_id <> 'publisher:feuerland:ark-nova-rules-v1.2'
  ) THEN
    RAISE EXCEPTION 'Ark Nova expansion or unrelated evidence must not be mixed into the reviewed rules';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id='publisher:feuerland:ark-nova-rules-v1.2'
      AND publisher_name='Feuerland Spiele'
      AND source_type='publisher_rulebook'
      AND url='https://www.feuerland-spiele.de/fileadmin/game/Arche_Nova/Arche_Nova_Rules_EN_Low_2022_01.pdf'
      AND revision_label='v1.2'
  ) THEN
    RAISE EXCEPTION 'Official Feuerland Ark Nova rulebook Version 1.2 source is required';
  END IF;

  UPDATE public.games
  SET content_review_status='human_reviewed',
      min_players=1,
      max_players=4,
      play_time=150,
      play_time_min_minutes=90,
      play_time_max_minutes=150,
      min_age=14,
      updated_at=now()
  WHERE id=v_game_id;

  IF NOT EXISTS (
    SELECT 1 FROM public.games WHERE id=v_game_id
      AND content_review_status='human_reviewed'
      AND min_players=1 AND max_players=4
      AND play_time=150 AND play_time_min_minutes=90 AND play_time_max_minutes=150
      AND min_age=14
  ) THEN
    RAISE EXCEPTION 'Ark Nova review or official product metadata update failed';
  END IF;
END $$;

COMMIT;
