BEGIN;

-- プレイヤー向け成功条件:
-- Gigamic の Papayoo 基本ゲームが、公式商品ページと 08-2024 公式ルールブックだけを根拠として、
-- 準備 → 最初のトリック → フォロー → トリックの勝者 → 得点 → ゲーム終了まで説明でき、
-- 3～8人・30分・7歳以上で検索公開されること。

INSERT INTO public.source_locators (
  locator_id, source_id, page_number, section_heading, external_reference
) VALUES
  ('papayoo:locator:first-trick-lead', 'papayoo:gigamic-rules-08-2024', 2, 'HOW TO PLAY', 'HOW TO PLAY — first trick'),
  ('papayoo:locator:trick-winner-next-lead', 'papayoo:gigamic-rules-08-2024', 2, 'HOW TO PLAY', 'HOW TO PLAY — trick winner'),
  ('papayoo:locator:game-rounds', 'papayoo:gigamic-rules-08-2024', 2, 'HOW TO PLAY / GAME END', 'HOW TO PLAY / GAME END — number of rounds and cumulative score')
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
  WHERE slug = 'papayoo'
  LIMIT 1;

  IF v_game_id IS NULL AND current_database() = 'source_bound_ruleset_test' THEN
    RAISE NOTICE 'Papayoo canonical game row is not part of the source-bound fixture; skipping review migration';
    RETURN;
  ELSIF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Papayoo game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND language_code = 'ja'
    AND edition_label = 'Gigamic Papayoo US rules 08-2024'
    AND platform = 'physical'
    AND revision_label = 'gigamic-papayoo-us-rules-08-2024-accessed-2026-08-26'
    AND verification_status = 'source_bound'
    AND source_ids = ARRAY['papayoo:gigamic-product','papayoo:gigamic-rules-08-2024']::text[]
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Source-bound Papayoo 08-2024 RuleSet is required';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 6 THEN
    RAISE EXCEPTION 'Papayoo requires exactly 6 existing source-bound RuleNodes before completion, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'papayoo:gigamic-rules-08-2024';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Papayoo contains supporting rule evidence from an unexpected source';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'papayoo:gigamic-product'
    AND source_type = 'publisher_product_page'
    AND platform = 'physical'
    AND url = 'https://en.gigamic.com/games-for-fun/84-papayoo.html';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Gigamic Papayoo product source is missing or changed';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_sources
  WHERE source_id = 'papayoo:gigamic-rules-08-2024'
    AND source_type = 'publisher_rulebook'
    AND platform = 'physical'
    AND revision_label = '08-2024'
    AND url = 'https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Expected Gigamic Papayoo 08-2024 rulebook source is missing or changed';
  END IF;

  -- 公式一次資料は英語。日本語表示用 RuleSet の言語とは分離する。
  UPDATE public.evidence_sources
  SET language_code = 'en', updated_at = now()
  WHERE source_id IN ('papayoo:gigamic-product','papayoo:gigamic-rules-08-2024');

  -- 表示順を「準備 → プレイ → 得点 → 終了」にそろえる。
  UPDATE public.rule_nodes SET sequence = 10, updated_at = now() WHERE rule_set_id = v_ruleset_id AND rule_id = 'goal-low-score';
  UPDATE public.rule_nodes SET sequence = 20, updated_at = now() WHERE rule_set_id = v_ruleset_id AND rule_id = 'setup-deck';
  UPDATE public.rule_nodes SET sequence = 30, updated_at = now() WHERE rule_set_id = v_ruleset_id AND rule_id = 'pass-left';
  UPDATE public.rule_nodes SET sequence = 40, updated_at = now() WHERE rule_set_id = v_ruleset_id AND rule_id = 'determine-papayoo';
  UPDATE public.rule_nodes SET sequence = 60, updated_at = now() WHERE rule_set_id = v_ruleset_id AND rule_id = 'follow-suit';
  UPDATE public.rule_nodes SET sequence = 80, updated_at = now() WHERE rule_set_id = v_ruleset_id AND rule_id = 'penalty-score';

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence, verification_status,
    source_claim_ref, evidence_ref, source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'first-trick-lead', 'turn',
      '各ラウンドの最初のトリックはディーラーが好きなカード1枚を表向きで出して始め、以後はディーラーの左隣から時計回りにカードを出す。',
      50, 'source_bound', 'papayoo:rule:first-trick-lead', 'papayoo:binding:first-trick-lead',
      'https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf',
      'papayoo:locator:first-trick-lead', '{"reviewed_from":"Gigamic Papayoo US Rules 08-2024"}'::jsonb),
    (v_ruleset_id, 'trick-winner-next-lead', 'turn',
      'トリックでは最初に出されたスートの中で最も数字が大きいカードを出したプレイヤーが中央のカードを取り、次のトリックを始める。最初に出されたスートを他の誰も出せなかった場合は、そのトリックを始めたプレイヤーがカードを取る。',
      70, 'source_bound', 'papayoo:rule:trick-winner-next-lead', 'papayoo:binding:trick-winner-next-lead',
      'https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf',
      'papayoo:locator:trick-winner-next-lead', '{"reviewed_from":"Gigamic Papayoo US Rules 08-2024"}'::jsonb),
    (v_ruleset_id, 'game-rounds', 'condition',
      'ゲーム開始時にプレイするラウンド数を決める。各ラウンドの最後に罰点をそれまでの合計へ加え、決めたラウンド数を終えた時点で合計点が最も少ないプレイヤーが勝つ。公式ルールは5ラウンドを目安としている。',
      90, 'source_bound', 'papayoo:rule:game-rounds', 'papayoo:binding:game-rounds',
      'https://export.gigamic.com/wp-content/uploads/2024/09/GIGAMIC_GBPA-EN_PAPAYOO-US_RULES_08-2024.pdf',
      'papayoo:locator:game-rounds', '{"reviewed_from":"Gigamic Papayoo US Rules 08-2024"}'::jsonb)
  ON CONFLICT (rule_set_id, rule_id) DO UPDATE SET
    node_type = EXCLUDED.node_type,
    normalized_statement = EXCLUDED.normalized_statement,
    sequence = EXCLUDED.sequence,
    verification_status = EXCLUDED.verification_status,
    source_claim_ref = EXCLUDED.source_claim_ref,
    evidence_ref = EXCLUDED.evidence_ref,
    source_url = EXCLUDED.source_url,
    source_locator = EXCLUDED.source_locator,
    metadata = EXCLUDED.metadata,
    updated_at = now();

  INSERT INTO public.claims (
    claim_id, rule_set_id, claim_type, normalized_payload, target_type, rule_id,
    lifecycle_status, generator_provenance
  )
  SELECT
    'papayoo:rule:' || rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', normalized_statement),
    'rule_node',
    rule_id,
    'accepted',
    '{"method":"human_reviewed_official_rulebook","source":"Gigamic Papayoo US Rules 08-2024"}'::jsonb
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND rule_id IN ('first-trick-lead','trick-winner-next-lead','game-rounds')
  ON CONFLICT (claim_id) DO UPDATE SET
    rule_set_id = EXCLUDED.rule_set_id,
    claim_type = EXCLUDED.claim_type,
    normalized_payload = EXCLUDED.normalized_payload,
    target_type = EXCLUDED.target_type,
    rule_id = EXCLUDED.rule_id,
    lifecycle_status = EXCLUDED.lifecycle_status,
    generator_provenance = EXCLUDED.generator_provenance,
    updated_at = now();

  INSERT INTO public.evidence_bindings (
    binding_id, claim_id, source_id, locator_id, relation,
    reviewer_provenance, generator_provenance, verified_at
  ) VALUES
    ('papayoo:binding:first-trick-lead', 'papayoo:rule:first-trick-lead', 'papayoo:gigamic-rules-08-2024', 'papayoo:locator:first-trick-lead', 'supports',
      '{"review":"human_reviewed","source":"Gigamic official rulebook"}'::jsonb,
      '{"migration":"104_review_papayoo_official_rules.sql"}'::jsonb, now()),
    ('papayoo:binding:trick-winner-next-lead', 'papayoo:rule:trick-winner-next-lead', 'papayoo:gigamic-rules-08-2024', 'papayoo:locator:trick-winner-next-lead', 'supports',
      '{"review":"human_reviewed","source":"Gigamic official rulebook"}'::jsonb,
      '{"migration":"104_review_papayoo_official_rules.sql"}'::jsonb, now()),
    ('papayoo:binding:game-rounds', 'papayoo:rule:game-rounds', 'papayoo:gigamic-rules-08-2024', 'papayoo:locator:game-rounds', 'supports',
      '{"review":"human_reviewed","source":"Gigamic official rulebook"}'::jsonb,
      '{"migration":"104_review_papayoo_official_rules.sql"}'::jsonb, now())
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    generator_provenance = EXCLUDED.generator_provenance,
    verified_at = EXCLUDED.verified_at;

  SELECT count(*) INTO v_count
  FROM public.rule_nodes
  WHERE rule_set_id = v_ruleset_id
    AND verification_status = 'source_bound';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Papayoo requires exactly 9 source-bound RuleNodes after completion, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.claims
  WHERE rule_set_id = v_ruleset_id
    AND lifecycle_status = 'accepted';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Papayoo requires exactly 9 accepted Claims after completion, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports';
  IF v_count <> 9 THEN
    RAISE EXCEPTION 'Papayoo requires exactly 9 supporting EvidenceBindings after completion, found %', v_count;
  END IF;

  SELECT count(*) INTO v_count
  FROM public.evidence_bindings eb
  JOIN public.claims c ON c.claim_id = eb.claim_id
  WHERE c.rule_set_id = v_ruleset_id
    AND c.lifecycle_status = 'accepted'
    AND eb.relation = 'supports'
    AND eb.source_id <> 'papayoo:gigamic-rules-08-2024';
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Papayoo contains supporting rule evidence from an unexpected source after completion';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      min_players = 3,
      max_players = 8,
      play_time = 30,
      play_time_min_minutes = 30,
      play_time_max_minutes = 30,
      min_age = 7,
      updated_at = now()
  WHERE id = v_game_id;

  IF NOT EXISTS (
    SELECT 1
    FROM public.games
    WHERE id = v_game_id
      AND content_review_status = 'human_reviewed'
      AND identity_status = 'verified'
      AND source_trust = 'official_publisher'
      AND edition_label = 'Gigamic Papayoo US rules 08-2024'
      AND language_code = 'ja'
      AND min_players = 3
      AND max_players = 8
      AND play_time = 30
      AND play_time_min_minutes = 30
      AND play_time_max_minutes = 30
      AND min_age = 7
      AND identity_source = 'https://en.gigamic.com/games-for-fun/84-papayoo.html'
      AND source_url = 'https://en.gigamic.com/games-for-fun/84-papayoo.html'
      AND amazon_url LIKE '%tag=bodogemikata-22%'
  ) THEN
    RAISE EXCEPTION 'Papayoo post-update verification failed';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id IN ('papayoo:gigamic-product','papayoo:gigamic-rules-08-2024')
      AND language_code <> 'en'
  ) THEN
    RAISE EXCEPTION 'Papayoo official source language must remain English';
  END IF;
END $$;

COMMIT;
