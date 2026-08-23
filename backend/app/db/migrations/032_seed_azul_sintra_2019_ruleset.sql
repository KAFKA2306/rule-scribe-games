BEGIN;

-- Azul: Stained Glass of Sintra Japanese physical edition sold by Hobby Japan from 2019.
-- Japanese product identity is bound to Hobby Japan's official catalog page.
-- Rule statements are normalized from Next Move Games' official English rulebook.
-- The rulebook URL is the publisher's currently hosted copy; the 2024 hosting path is not
-- treated as a distinct gameplay edition. Azul, other Azul titles, variants, and fan rules
-- are deliberately excluded from this base RuleSet.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:hobbyjapan:azul-sintra:2019-product',
    'https://hobbyjapan.games/azul_stained_glass_of_sintra/',
    'Hobby Japan アズール：シントラのステンドグラス official product page',
    'publisher_product_page',
    'Hobby Japan / Next Move Games',
    'physical',
    'ja',
    '2019-02',
    '{"authority":"publisher","role":"canonical_japanese_product_identity","audit_date":"2026-08-23","notes":"Hobby Japan identifies the Japanese edition as a standalone Next Move Games title released 2019-02; 2-4 players; 30-45 minutes; age 8+","excludes":["Azul base game","Azul expansions","other Azul standalone titles","fan variants"]}'::jsonb
  ),
  (
    'publisher:nextmove:azul-sintra:official-rulebook',
    'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf',
    'Next Move Games Azul: Stained Glass of Sintra official English rulebook',
    'publisher_rulebook',
    'Next Move Games',
    'physical',
    'en',
    'current-hosted-copy',
    '{"authority":"publisher","role":"gameplay_rules","audit_date":"2026-08-23","notes":"Official rulebook linked from the current Next Move Games product page; URL hosting date is not promoted to a separate gameplay edition"}'::jsonb
  )
ON CONFLICT (source_id) DO UPDATE SET
  url = EXCLUDED.url,
  document_identity = EXCLUDED.document_identity,
  source_type = EXCLUDED.source_type,
  publisher_name = EXCLUDED.publisher_name,
  platform = EXCLUDED.platform,
  language_code = EXCLUDED.language_code,
  revision_label = EXCLUDED.revision_label,
  trust_metadata = EXCLUDED.trust_metadata,
  updated_at = now();

INSERT INTO public.source_locators (
  locator_id, source_id, page_number, section_heading, external_reference
)
VALUES
  ('azul-sintra:product:jp-identity', 'publisher:hobbyjapan:azul-sintra:2019-product', NULL, 'アズール：シントラのステンドグラス', 'Japanese edition; Next Move Games; sold by Hobby Japan; released 2019-02; 2-4 players; 30-45 minutes; age 8+; standalone title'),
  ('azul-sintra:rulebook:setup', 'publisher:nextmove:azul-sintra:official-rulebook', 2, 'Game Setup', 'Use 5/7/9 Factory displays for 2/3/4 players; choose common palace-board side; randomize 8 pattern strips; place glazier on leftmost strip; prepare score/broken-glass tracks and round indicator; fill each Factory with 4 panes'),
  ('azul-sintra:rulebook:rounds-actions', 'publisher:nextmove:azul-sintra:official-rulebook', 3, 'Object of the game / Playing the game', 'Game lasts 6 rounds; on a turn either Advance a pattern or move the glazier back to the leftmost pattern strip'),
  ('azul-sintra:rulebook:draft', 'publisher:nextmove:azul-sintra:official-rulebook', 3, 'Step 1 - Pick pane pieces of one color', 'Take all panes of one color from one Factory and move the rest to center, or take all of one color from center; first center drafter also takes starting-player tile and advances broken-glass track one space'),
  ('azul-sintra:rulebook:place', 'publisher:nextmove:azul-sintra:official-rulebook', 4, 'Step 2 - Place the pane pieces on one of your pattern strips', 'All drafted panes go to one reachable matching pattern strip at or to the right of the glazier; excess panes break and advance broken-glass track'),
  ('azul-sintra:rulebook:complete', 'publisher:nextmove:azul-sintra:official-rulebook', 4, 'Step 3 - Check if the pattern is complete', 'When all 5 spaces fill, immediately score round-color bonus, keep one pane for the window, discard four, flip/remove strip as appropriate, and score that window plus occupied windows to its right'),
  ('azul-sintra:rulebook:reset-glazier', 'publisher:nextmove:azul-sintra:official-rulebook', 5, 'Move your glazier back to the leftmost pattern strip', 'Instead of drafting, move glazier to the leftmost remaining pattern strip; unavailable if already there'),
  ('azul-sintra:rulebook:round-end', 'publisher:nextmove:azul-sintra:official-rulebook', 5, 'End of the round', 'Round ends when Factory displays and center are empty; remove the top round-indicator pane; unless round 6 is complete, refill Factories with 4 panes and continue'),
  ('azul-sintra:rulebook:final', 'publisher:nextmove:azul-sintra:official-rulebook', 5, 'End of the game', 'After round 6: gain 1 point per 3 panes left on pattern strips, lose current broken-glass penalty, then score palace-board side bonus'),
  ('azul-sintra:rulebook:side-b-victory', 'publisher:nextmove:azul-sintra:official-rulebook', 6, 'End of the game', 'Side A ornament scoring; Side B completed-windows × chosen-color panes; highest score wins; tie broken by fewer broken-glass points lost, otherwise shared victory')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
  page_number = EXCLUDED.page_number,
  section_heading = EXCLUDED.section_heading,
  external_reference = EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_work_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT g.id, g.work_id INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'azul-stained-glass-of-sintra'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Azul Sintra Game/Work row is required before applying RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://hobbyjapan.games/azul_stained_glass_of_sintra/',
    source_url = 'https://hobbyjapan.games/azul_stained_glass_of_sintra/',
    source_trust = 'official_publisher',
    edition_label = 'ホビージャパン日本語版 (2019)',
    language_code = 'ja',
    publisher = 'Hobby Japan / Next Move Games',
    published_year = 2019,
    min_players = 2,
    max_players = 4,
    play_time = 45,
    min_age = 8,
    source_revision = 'Hobby Japan 2019 Japanese product identity + Next Move Games official rulebook',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'ホビージャパン日本語版 (2019)'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2019-hobbyjapan-ja'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'ホビージャパン日本語版 (2019)',
      'Hobby Japan 2019 Japanese product identity + Next Move Games official rulebook',
      true, '2019-hobbyjapan-ja', 'physical', 'Hobby Japan / Next Move Games',
      'active', 'source_bound',
      ARRAY[
        'publisher:hobbyjapan:azul-sintra:2019-product',
        'publisher:nextmove:azul-sintra:official-rulebook'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Hobby Japan 2019 Japanese product identity + Next Move Games official rulebook',
      is_active = true,
      publisher_name = 'Hobby Japan / Next Move Games',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:hobbyjapan:azul-sintra:2019-product',
        'publisher:nextmove:azul-sintra:official-rulebook'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'setup.factories-and-palace', 'setup', '工房展示ボードは2人戦5枚、3人戦7枚、4人戦9枚を使用する。各プレイヤーは同じ面の宮殿ボードを使い、自色の図案票8枚をランダムに各尖塔へ置き、ガラス職人コマを最左の図案票の上に置く。得点・割れたガラス・ラウンド表示を準備し、各工房に袋からガラス片4個ずつを置く。', 0, 'source_bound', 'azul-sintra:rule:setup.factories-and-palace', 'azul-sintra:binding:setup.factories-and-palace', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:setup', '{}'::jsonb),
    (v_ruleset_id, 'game.six-rounds', 'game_end', 'ゲームは全6ラウンドで行い、第6ラウンド終了後に最終得点計算を行う。', 0, 'source_bound', 'azul-sintra:rule:game.six-rounds', 'azul-sintra:binding:game.six-rounds', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:rounds-actions', '{}'::jsonb),
    (v_ruleset_id, 'turn.choose-action', 'turn', '自分の手番では「図案を進める」か「ガラス職人コマを最も左の残っている図案票へ戻す」のどちらか一方を行う。', 0, 'source_bound', 'azul-sintra:rule:turn.choose-action', 'azul-sintra:binding:turn.choose-action', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:rounds-actions', '{}'::jsonb),
    (v_ruleset_id, 'action.draft-one-color', 'action', '図案を進める場合、工房展示ボード1枚から1色のガラス片をすべて取り残りを中央へ移すか、中央から1色をすべて取る。各ラウンドで最初に中央から取ったプレイヤーは先手プレイヤータイルも受け取り、割れたガラストラックを1スペース下げる。', 0, 'source_bound', 'azul-sintra:rule:action.draft-one-color', 'azul-sintra:binding:action.draft-one-color', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:draft', '{}'::jsonb),
    (v_ruleset_id, 'action.place-reachable-strip', 'action', '取ったガラス片はすべて1枚の図案票へ置く。その図案票はガラス職人コマの真下または右側で到達でき、各ガラス片は対応色の空きマスへ置く。右側の図案票を使うなら先にガラス職人コマをそこへ移動する。', 1, 'source_bound', 'azul-sintra:rule:action.place-reachable-strip', 'azul-sintra:binding:action.place-reachable-strip', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:place', '{}'::jsonb),
    (v_ruleset_id, 'action.excess-breaks', 'effect', '選んだ図案票に置けない余剰ガラス片は1個ごとに割れたガラストラックを1スペース下げ、グラスタワーへ入れる。到達可能な図案票に対応色の空きマスがある限り、置けるガラス片を任意に全部割ることはできない。', 2, 'source_bound', 'azul-sintra:rule:action.excess-breaks', 'azul-sintra:binding:action.excess-breaks', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:place', '{}'::jsonb),
    (v_ruleset_id, 'scoring.complete-pattern-immediately', 'scoring', '図案票の5マスが埋まったら、その手番中にただちに完成処理を行う。まず現在のラウンド表示色と一致するガラス片1個につき1点を得る。次に5個のうち1個を窓へ残して4個をグラスタワーへ入れ、窓が初回なら図案票を裏返し、2回目なら窓を完成させて図案票を取り除く。最後にその窓の印刷点と、右側で1個以上ガラス片が置かれた各窓の印刷点を加える。', 0, 'source_bound', 'azul-sintra:rule:scoring.complete-pattern-immediately', 'azul-sintra:binding:scoring.complete-pattern-immediately', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:complete', '{"corrects_legacy":"pattern completion scoring is immediate, not deferred to round end"}'::jsonb),
    (v_ruleset_id, 'action.reset-glazier', 'action', 'ガラス片を取る代わりに、ガラス職人コマを最も左に残っている図案票の上へ戻して手番を終えられる。ただし既にその位置にいる場合、このアクションは選べない。', 3, 'source_bound', 'azul-sintra:rule:action.reset-glazier', 'azul-sintra:binding:action.reset-glazier', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:reset-glazier', '{}'::jsonb),
    (v_ruleset_id, 'round-end.empty-and-refill', 'round_end', '工房展示ボードと中央のガラス片がすべてなくなるとラウンド終了。ラウンド表示の先頭のガラス片を1個取り除き、第6ラウンド後でなければ先手プレイヤータイルを持つプレイヤーが各工房へガラス片4個ずつ補充して次ラウンドを始める。袋が空ならグラスタワーのガラス片を袋へ戻して補充を続ける。', 0, 'source_bound', 'azul-sintra:rule:round-end.empty-and-refill', 'azul-sintra:binding:round-end.empty-and-refill', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:round-end', '{}'::jsonb),
    (v_ruleset_id, 'victory.final-scoring', 'victory', '第6ラウンド後、図案票に残ったガラス片3個につき1点を得て、割れたガラストラックが示す点を失う。さらに宮殿ボードA面なら各装飾枠の充足数で0/3/6/10点、B面なら完成した窓数と選んだ1色の窓上ガラス片数を掛けた点を加える。最終得点が最も高いプレイヤーが勝ち、同点なら割れたガラスで失った点が少ない方が勝つ。それでも同点なら勝利を共有する。', 0, 'source_bound', 'azul-sintra:rule:victory.final-scoring', 'azul-sintra:binding:victory.final-scoring', 'https://cdn.svc.asmodee.net/production-nextmove/uploads/sites/4/2024/06/EN-Azul-Sintra-Rules_2024_compressed.pdf', 'azul-sintra:rulebook:side-b-victory', '{}'::jsonb)
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
    claim_id, rule_set_id, claim_type, normalized_payload, target_type,
    rule_id, lifecycle_status, generator_provenance
  )
  SELECT
    'azul-sintra:rule:' || rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_source_normalization","audit_date":"2026-08-23","scope":"2019_hobbyjapan_japanese_physical"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id IN (
      'setup.factories-and-palace','game.six-rounds','turn.choose-action','action.draft-one-color',
      'action.place-reachable-strip','action.excess-breaks','scoring.complete-pattern-immediately',
      'action.reset-glazier','round-end.empty-and-refill','victory.final-scoring'
    )
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
    ('azul-sintra:binding:setup.factories-and-palace','azul-sintra:rule:setup.factories-and-palace','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:setup','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:game.six-rounds','azul-sintra:rule:game.six-rounds','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:rounds-actions','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:turn.choose-action','azul-sintra:rule:turn.choose-action','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:rounds-actions','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:action.draft-one-color','azul-sintra:rule:action.draft-one-color','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:draft','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:action.place-reachable-strip','azul-sintra:rule:action.place-reachable-strip','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:place','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:action.excess-breaks','azul-sintra:rule:action.excess-breaks','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:place','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:scoring.complete-pattern-immediately','azul-sintra:rule:scoring.complete-pattern-immediately','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:complete','supports','{"review":"publisher_source","corrects_legacy":"immediate_pattern_completion_scoring"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:action.reset-glazier','azul-sintra:rule:action.reset-glazier','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:reset-glazier','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:round-end.empty-and-refill','azul-sintra:rule:round-end.empty-and-refill','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:round-end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('azul-sintra:binding:victory.final-scoring','azul-sintra:rule:victory.final-scoring','publisher:nextmove:azul-sintra:official-rulebook','azul-sintra:rulebook:side-b-victory','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT (binding_id) DO UPDATE SET
    claim_id = EXCLUDED.claim_id,
    source_id = EXCLUDED.source_id,
    locator_id = EXCLUDED.locator_id,
    relation = EXCLUDED.relation,
    reviewer_provenance = EXCLUDED.reviewer_provenance,
    generator_provenance = EXCLUDED.generator_provenance,
    verified_at = EXCLUDED.verified_at;
END $$;

COMMIT;