BEGIN;

-- プレイヤー向け成功条件:
-- Forest Shuffle基本ゲームがLookout Gamesの現行公式資料だけを根拠として、
-- 準備 → 手番の選択 → カード配置 → 終了 → 勝敗まで説明でき、検索公開されること。
-- 旧版にあった初期手札のmulliganは現行FAQで削除済みのため、現行ルールとして復活させない。

INSERT INTO public.source_locators
  (locator_id, source_id, page_number, section_heading, external_reference)
VALUES
  ('forest-shuffle:locator:setup-current',
   'forest-shuffle:lookout-rulebook', NULL, 'Setup',
   'Current official base rules: Setup'),
  ('forest-shuffle:locator:draw-two',
   'forest-shuffle:lookout-rulebook', NULL, 'Game Flow / A) Drawing Two Cards',
   'Current official base rules: Game Flow / A) Drawing Two Cards'),
  ('forest-shuffle:locator:no-mulligan-current',
   'forest-shuffle:lookout-product', NULL,
   'FAQ / There are differences in the rulebooks: Is playing mulligan mandatory - or not?',
   'Current publisher FAQ: mulligan removed from the official rules')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
  page_number = EXCLUDED.page_number,
  section_heading = EXCLUDED.section_heading,
  external_reference = EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_count integer;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'forest-shuffle'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Forest Shuffle canonical game row is not part of the source-bound fixture; skipping completion';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Forest Shuffle game row is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND title = 'Forest Shuffle'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'review_required'
      AND identity_source = 'https://www.lookout-spiele.de/en/games/forrestshuffle.html'
      AND min_players = 2
      AND max_players = 5
      AND play_time = 60
      AND play_time_min_minutes = 60
      AND play_time_max_minutes = 60
      AND min_age = 10
      AND published_year = 2023
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Canonical Forest Shuffle identity, metadata, monetization path, or review state changed; re-audit before publishing';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'Lookout Forest Shuffle base game 2023 / current official rules'
    AND platform = 'physical'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY[
      'forest-shuffle:lookout-product',
      'forest-shuffle:lookout-rulebook'
    ]::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Forest Shuffle current base RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 6 THEN
    RAISE EXCEPTION 'Forest Shuffle expected exactly 6 source-bound RuleNodes before completion, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 6 THEN
    RAISE EXCEPTION 'Forest Shuffle expected exactly 6 accepted Claims before completion, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 6 THEN
    RAISE EXCEPTION 'Forest Shuffle expected exactly 6 supporting EvidenceBindings before completion, found %', v_count;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'forest-shuffle:lookout-rulebook'
      AND source_type = 'publisher_rulebook'
      AND platform = 'physical'
      AND language_code = 'en'
      AND url = 'https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf'
  ) THEN
    RAISE EXCEPTION 'Current Lookout Forest Shuffle base rulebook source is missing or changed';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.evidence_sources
    WHERE source_id = 'forest-shuffle:lookout-product'
      AND source_type = 'publisher_product_page'
      AND platform = 'physical'
      AND language_code = 'en'
      AND url = 'https://www.lookout-spiele.de/en/games/forrestshuffle.html'
  ) THEN
    RAISE EXCEPTION 'Current Lookout Forest Shuffle product/FAQ source is missing or changed';
  END IF;

  INSERT INTO public.rule_nodes
    (rule_set_id, rule_id, node_type, normalized_statement, sequence, verification_status,
     source_claim_ref, evidence_ref, source_url, source_locator, metadata)
  VALUES
    (v_ruleset_id, 'setup-current', 'setup',
     '準備ではclearingをプレイエリア中央に置き、各プレイヤーはcave cardを自分の前に置いて6枚を手札にする。',
     5, 'source_bound', 'forest-shuffle:rule:setup-current', 'forest-shuffle:binding:setup-current',
     'https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf',
     'forest-shuffle:locator:setup-current', '{}'::jsonb),
    (v_ruleset_id, 'draw-two', 'action',
     '手番では「2枚引く」か「カードを1枚プレイしてclearingを確認する」のどちらか1つを行う。2枚引く場合は、1枚ごとに山札の一番上またはclearingの表向きカードから選ぶ。',
     15, 'source_bound', 'forest-shuffle:rule:draw-two', 'forest-shuffle:binding:draw-two',
     'https://www.lookout-spiele.de/upload/en_forrestshuffle.html_Forest_Shuffle_175_Rules_EN_WEB_260209.pdf',
     'forest-shuffle:locator:draw-two', '{}'::jsonb),
    (v_ruleset_id, 'no-mulligan-current', 'exception',
     'Lookout Gamesの現行公式ルールでは、初期手札に木がない場合に6枚すべてを交換する旧mulliganルールは削除されている。',
     17, 'source_bound', 'forest-shuffle:rule:no-mulligan-current', 'forest-shuffle:binding:no-mulligan-current',
     'https://www.lookout-spiele.de/en/games/forrestshuffle.html',
     'forest-shuffle:locator:no-mulligan-current', '{}'::jsonb);

  INSERT INTO public.claims
    (claim_id, rule_set_id, claim_type, normalized_payload, target_type, rule_id,
     lifecycle_status, generator_provenance)
  SELECT 'forest-shuffle:rule:' || rule_id,
         v_ruleset_id,
         'normalized_rule_statement',
         jsonb_build_object('statement', normalized_statement),
         'rule_node',
         rule_id,
         'accepted',
         '{"method":"human_reviewed_official_sources","source":"Lookout Games current official base rules and FAQ"}'::jsonb
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND rule_id IN ('setup-current', 'draw-two', 'no-mulligan-current');

  INSERT INTO public.evidence_bindings
    (binding_id, claim_id, source_id, locator_id, relation,
     reviewer_provenance, generator_provenance, verified_at)
  VALUES
    ('forest-shuffle:binding:setup-current',
     'forest-shuffle:rule:setup-current',
     'forest-shuffle:lookout-rulebook',
     'forest-shuffle:locator:setup-current',
     'supports',
     '{"review":"human_reviewed","source":"official_rulebook"}'::jsonb,
     '{"migration":"114_complete_forest_shuffle_current_rules.sql"}'::jsonb,
     now()),
    ('forest-shuffle:binding:draw-two',
     'forest-shuffle:rule:draw-two',
     'forest-shuffle:lookout-rulebook',
     'forest-shuffle:locator:draw-two',
     'supports',
     '{"review":"human_reviewed","source":"official_rulebook"}'::jsonb,
     '{"migration":"114_complete_forest_shuffle_current_rules.sql"}'::jsonb,
     now()),
    ('forest-shuffle:binding:no-mulligan-current',
     'forest-shuffle:rule:no-mulligan-current',
     'forest-shuffle:lookout-product',
     'forest-shuffle:locator:no-mulligan-current',
     'supports',
     '{"review":"human_reviewed","source":"official_publisher_faq"}'::jsonb,
     '{"migration":"114_complete_forest_shuffle_current_rules.sql"}'::jsonb,
     now());

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Forest Shuffle publication requires exactly 9 source-bound RuleNodes, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Forest Shuffle publication requires exactly 9 accepted Claims, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Forest Shuffle publication requires exactly 9 supporting EvidenceBindings, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id NOT IN ('forest-shuffle:lookout-rulebook', 'forest-shuffle:lookout-product');
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Forest Shuffle current base rules contain support outside Lookout Games official sources';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND rule_id = 'no-mulligan-current'
      AND normalized_statement LIKE '%mulligan%削除%'
      AND source_locator = 'forest-shuffle:locator:no-mulligan-current'
  ) THEN
    RAISE EXCEPTION 'Forest Shuffle current mulligan-removal boundary is missing';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND content_review_status = 'human_reviewed'
      AND min_players = 2
      AND max_players = 5
      AND play_time = 60
      AND min_age = 10
      AND published_year = 2023
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Forest Shuffle review promotion or canonical metadata preservation failed';
  END IF;
END $$;

COMMIT;
