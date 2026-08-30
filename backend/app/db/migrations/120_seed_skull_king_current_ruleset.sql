BEGIN;

-- Skull King current physical edition, normalized from Grandpa Beck's Games
-- current English rulebook and current first-party rules/FAQ page.
-- Optional Advanced Play cards and earlier editions are deliberately excluded
-- from this base RuleSet. Two-player rules remain explicit player-count
-- conditions instead of being blended into the normal 3+ player flow.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:grandpa-becks:skull-king:current-product',
    'https://www.grandpabecksgames.com/products/copy-of-skull-king%C2%AE',
    'Grandpa Beck''s Games Skull King current product page',
    'publisher_product_page',
    'Grandpa Beck''s Games',
    'physical',
    'en',
    'current-2026-08-31',
    '{"authority":"publisher","role":"current_product_identity","audit_date":"2026-08-31","excludes":["earlier editions","digital implementations"]}'::jsonb
  ),
  (
    'publisher:grandpa-becks:skull-king:current-rulebook',
    'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570',
    'Grandpa Beck''s Games Skull King Simplified Rulebook US WEB',
    'publisher_rulebook',
    'Grandpa Beck''s Games',
    'physical',
    'en',
    'current-web-rulebook-1764178570',
    '{"authority":"publisher","role":"current_base_and_two_player_rules","audit_date":"2026-08-31","notes":"Advanced Play starts on printed page 16 and is excluded from the base projection"}'::jsonb
  ),
  (
    'publisher:grandpa-becks:skull-king:current-rules-faq',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Grandpa Beck''s Games Skull King current rules and FAQ page',
    'publisher_rules_faq_page',
    'Grandpa Beck''s Games',
    'physical',
    'en',
    'accessed-2026-08-31',
    '{"authority":"publisher","role":"current_rulebook_index_and_faq_clarifications","audit_date":"2026-08-31","notes":"The separate /pages/faq-skull-king page did not expose FAQ content when audited; current FAQ clarifications are bound to the Skull King rules page instead"}'::jsonb
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
  ('skull-king:product:identity', 'publisher:grandpa-becks:skull-king:current-product', NULL, 'Skull King', 'Grandpa Beck''s Games current physical product identity'),
  ('skull-king:rulebook:setup', 'publisher:grandpa-becks:skull-king:current-rulebook', 5, 'SETUP', 'Remove blank cards, Loot, Kraken and White Whale before normal play; those cards are optional Advanced Rules; deal by round number; 8-player rounds 9 and 10 use 8 cards each'),
  ('skull-king:rulebook:bidding', 'publisher:grandpa-becks:skull-king:current-rulebook', 6, 'BIDDING', 'After examining the dealt hand, each player predicts the number of tricks they will win and reveals the bid simultaneously'),
  ('skull-king:rulebook:playing', 'publisher:grandpa-becks:skull-king:current-rulebook', 7, 'PLAYING', 'Clockwise trick play; suited cards must follow the led suit when a suited card is chosen and the player holds that suit; special cards may be played on any turn; trick winner leads next trick'),
  ('skull-king:rulebook:suited-cards', 'publisher:grandpa-becks:skull-king:current-rulebook', 8, 'SUITED CARDS', 'Three standard suits and black trump; numbered cards 1-14; follow-suit rule for suited cards'),
  ('skull-king:rulebook:special-cards', 'publisher:grandpa-becks:skull-king:current-rulebook', 10, 'SPECIAL CARDS', 'Pirate, Tigress, Skull King and Mermaid hierarchy; Mermaid wins a trick containing Pirate + Skull King + Mermaid regardless of play order'),
  ('skull-king:rulebook:leading-end', 'publisher:grandpa-becks:skull-king:current-rulebook', 11, 'LEADING WITH SPECIAL CARDS / ENDING THE GAME', 'Escape defers lead suit; character lead has no lead suit; game ends after ten rounds and ties continue with another round'),
  ('skull-king:rulebook:scoring', 'publisher:grandpa-becks:skull-king:current-rulebook', 12, 'SCORING', 'Correct bid of one or more scores 20 per trick; incorrect bid loses 10 per trick difference; zero bid success/failure is ±10 times cards dealt'),
  ('skull-king:rulebook:bonus', 'publisher:grandpa-becks:skull-king:current-rulebook', 13, 'BONUS POINTS', 'Bonus points are earned only if the player gets their bid; suited 14 and character-capture bonuses are listed'),
  ('skull-king:rulebook:two-player', 'publisher:grandpa-becks:skull-king:current-rulebook', 15, 'TWO-PLAYER RULES', 'Deal a third face-down Graybeard hand; Graybeard always plays second; Graybeard need not follow suit; Tigress acts as Escape for Graybeard; Loot is not used'),
  ('skull-king:faq:pirate-powers', 'publisher:grandpa-becks:skull-king:current-rules-faq', NULL, 'FAQ / Pirate Powers', 'Pirate powers are generally used immediately after winning a trick with that Pirate; Harry the Giant is resolved after the last trick'),
  ('skull-king:faq:graybeard-tigress', 'publisher:grandpa-becks:skull-king:current-rules-faq', NULL, 'FAQ / Graybeard', 'When Graybeard plays the Tigress in two-player play, it acts as an Escape'),
  ('skull-king:faq:mermaid-triad', 'publisher:grandpa-becks:skull-king:current-rules-faq', NULL, 'FAQ / Mermaid', 'If Mermaid, Skull King and Pirate are in the same trick, Mermaid wins regardless of order')
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
  SELECT g.id, g.work_id
    INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'skull-king'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Skull King Game/Work row is required before applying the current RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://www.grandpabecksgames.com/products/copy-of-skull-king%C2%AE',
    source_url = 'https://www.grandpabecksgames.com/pages/skull-king',
    source_trust = 'official_publisher',
    edition_label = 'Grandpa Beck''s Games current edition',
    language_code = 'en',
    publisher = 'Grandpa Beck''s Games',
    source_revision = 'current English rulebook web revision 1764178570; rules/FAQ accessed 2026-08-31',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'en'
    AND COALESCE(rs.edition_label, '') = 'Grandpa Beck''s Games current edition'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = 'current-web-rulebook-1764178570'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'en', 'Grandpa Beck''s Games current edition',
      'current English rulebook web revision 1764178570; rules/FAQ accessed 2026-08-31',
      true, 'current-web-rulebook-1764178570', 'physical', 'Grandpa Beck''s Games',
      'active', 'source_bound',
      ARRAY[
        'publisher:grandpa-becks:skull-king:current-product',
        'publisher:grandpa-becks:skull-king:current-rulebook',
        'publisher:grandpa-becks:skull-king:current-rules-faq'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'current English rulebook web revision 1764178570; rules/FAQ accessed 2026-08-31',
      is_active = true,
      publisher_name = 'Grandpa Beck''s Games',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:grandpa-becks:skull-king:current-product',
        'publisher:grandpa-becks:skull-king:current-rulebook',
        'publisher:grandpa-becks:skull-king:current-rules-faq'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'setup.base-deck', 'setup',
      '通常ゲームでは、開始前にBlank、Loot、Kraken、White Whaleを山札から除く。これらはAdvanced Rulesで使う任意カードであり、通常ルールには含めない。',
      0, 'source_bound', 'skull-king:current:rule:setup.base-deck', 'skull-king:current:binding:setup.base-deck',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:setup',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'setup.round-deal', 'setup',
      'ゲームは10ラウンド行う。第1ラウンドは各1枚、第2ラウンドは各2枚というように、原則としてラウンド番号と同じ枚数を各プレイヤーへ配る。',
      1, 'source_bound', 'skull-king:current:rule:setup.round-deal', 'skull-king:current:binding:setup.round-deal',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:setup',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'setup.eight-player-cap', 'exception',
      '8人戦ではカード枚数の都合により、第9ラウンドと第10ラウンドも各プレイヤーへ8枚ずつ配る。',
      2, 'source_bound', 'skull-king:current:rule:setup.eight-player-cap', 'skull-king:current:binding:setup.eight-player-cap',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:setup',
      '{"condition":{"player_count":8},"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'round.bid', 'phase',
      '各ラウンドで手札を確認した後、そのラウンドで自分が取ると予想するトリック数を決め、全員が同時にビッドを公開する。',
      0, 'source_bound', 'skull-king:current:rule:round.bid', 'skull-king:current:binding:round.bid',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:bidding',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'turn.follow-suit', 'condition',
      '数字カードがリードされた場合、数字カードを出すなら、手札にリードされたスートがある限り同じスートを出す。特殊カードはリードスートに関係なく出せる。',
      1, 'source_bound', 'skull-king:current:rule:turn.follow-suit', 'skull-king:current:binding:turn.follow-suit',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:playing',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'turn.special-lead', 'exception',
      'EscapeまたはEscapeとして使うTigressが最初に出た場合は、次に通常の数字カードを出したプレイヤーがリードスートを決める。Mermaid、Pirate、Skull King、Pirateとして使うTigressが最初なら、そのトリックにリードスートはない。',
      2, 'source_bound', 'skull-king:current:rule:turn.special-lead', 'skull-king:current:binding:turn.special-lead',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:leading-end',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'resolution.pirate', 'conflict_resolution',
      'Pirateはすべての数字カードより強い。同じトリックにPirateが複数枚ある場合、先に出されたPirateが上位になる。',
      3, 'source_bound', 'skull-king:current:rule:resolution.pirate', 'skull-king:current:binding:resolution.pirate',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:special-cards',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'resolution.skull-king', 'conflict_resolution',
      'Skull Kingはすべての数字カードとPirateより強いが、Mermaidには負ける。',
      4, 'source_bound', 'skull-king:current:rule:resolution.skull-king', 'skull-king:current:binding:resolution.skull-king',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:special-cards',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'resolution.mermaid', 'conflict_resolution',
      'MermaidはSkull Kingとすべての数字カードより強いが、Pirateには負ける。同じトリックにMermaidが複数枚ある場合、先に出されたMermaidが上位になる。',
      5, 'source_bound', 'skull-king:current:rule:resolution.mermaid', 'skull-king:current:binding:resolution.mermaid',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:special-cards',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'resolution.mermaid-triad', 'exception',
      '同じトリックにMermaid、Skull King、Pirateがすべて出た場合は、出した順番に関係なくMermaidがそのトリックに勝つ。',
      6, 'source_bound', 'skull-king:current:rule:resolution.mermaid-triad', 'skull-king:current:binding:resolution.mermaid-triad',
      'https://www.grandpabecksgames.com/pages/skull-king', 'skull-king:faq:mermaid-triad',
      '{"scope":"base","clarification":"publisher_faq","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'scoring.bid-one-plus', 'scoring',
      '1以上をビッドしたプレイヤーが予想どおりのトリック数を取ると、取ったトリック1つにつき20点を得る。予想と違った場合は、差1トリックにつき10点を失う。',
      0, 'source_bound', 'skull-king:current:rule:scoring.bid-one-plus', 'skull-king:current:binding:scoring.bid-one-plus',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:scoring',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'scoring.zero-bid', 'scoring',
      '0をビッドして0トリックなら、そのラウンドで配られたカード枚数の10倍を得る。0をビッドして1トリック以上取った場合は、配られたカード枚数の10倍を失う。',
      1, 'source_bound', 'skull-king:current:rule:scoring.zero-bid', 'skull-king:current:binding:scoring.zero-bid',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:scoring',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'scoring.bonus-gate', 'scoring',
      'ボーナスポイントは、そのラウンドで自分のビッドどおりのトリック数を取れた場合にだけ得られる。',
      2, 'source_bound', 'skull-king:current:rule:scoring.bonus-gate', 'skull-king:current:binding:scoring.bonus-gate',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:bonus',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'game-end.ten-rounds', 'game_end',
      '10ラウンド終了時に合計得点を比べる。同点の場合は、同点が解消されるまで追加ラウンドを行う。',
      0, 'source_bound', 'skull-king:current:rule:game-end.ten-rounds', 'skull-king:current:binding:game-end.ten-rounds',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:leading-end',
      '{"scope":"base","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'two-player.graybeard-hand', 'exception',
      '2人戦では3つ目の手札を裏向きで配り、Graybeardの手札として使う。Graybeardは誰がリードしても常にトリックの2番目にカードを出し、リードスートに従う必要はない。',
      10, 'source_bound', 'skull-king:current:rule:two-player.graybeard-hand', 'skull-king:current:binding:two-player.graybeard-hand',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:two-player',
      '{"condition":{"player_count":2},"scope":"two_player","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'two-player.graybeard-lead', 'exception',
      '2人戦でGraybeardがトリックに勝った場合、次のトリックはGraybeardが最初にカードを出し、そのラウンドの人間側リードプレイヤーが2番目にカードを出す。',
      11, 'source_bound', 'skull-king:current:rule:two-player.graybeard-lead', 'skull-king:current:binding:two-player.graybeard-lead',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:two-player',
      '{"condition":{"player_count":2},"scope":"two_player","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'two-player.tigress', 'exception',
      '2人戦でGraybeardがTigressを出した場合、そのTigressはEscapeとして扱う。',
      12, 'source_bound', 'skull-king:current:rule:two-player.tigress', 'skull-king:current:binding:two-player.tigress',
      'https://www.grandpabecksgames.com/pages/skull-king', 'skull-king:faq:graybeard-tigress',
      '{"condition":{"player_count":2},"scope":"two_player","clarification":"publisher_faq","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'two-player.no-loot', 'exception',
      '2人戦ではLootカードを使用しない。',
      13, 'source_bound', 'skull-king:current:rule:two-player.no-loot', 'skull-king:current:binding:two-player.no-loot',
      'https://cdn.shopify.com/s/files/1/0565/3230/4053/files/Skull_King_Simplified_Rulebook_US_WEB_NO_CROP_a0eb3b84-f1cd-4087-8bda-0aab43d231af.pdf?v=1764178570', 'skull-king:rulebook:two-player',
      '{"condition":{"player_count":2},"scope":"two_player","source_language":"en","normalized_language":"ja"}'::jsonb),
    (v_ruleset_id, 'faq.pirate-power-timing', 'exception',
      'Pirateの固有能力は原則として、そのPirateでトリックに勝った直後に解決する。Harry the Giantの能力だけは最後のトリック後に解決する。',
      14, 'source_bound', 'skull-king:current:rule:faq.pirate-power-timing', 'skull-king:current:binding:faq.pirate-power-timing',
      'https://www.grandpabecksgames.com/pages/skull-king', 'skull-king:faq:pirate-powers',
      '{"scope":"base","clarification":"publisher_faq","source_language":"en","normalized_language":"ja"}'::jsonb)
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
    'skull-king:current:rule:' || rn.rule_id,
    v_ruleset_id,
    'rule_statement',
    jsonb_build_object(
      'statement', rn.normalized_statement,
      'source_scope', COALESCE(rn.metadata->>'scope', 'base'),
      'condition', COALESCE(rn.metadata->'condition', 'null'::jsonb)
    ),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"seed":"032_seed_skull_king_current_ruleset","audit_date":"2026-08-31","method":"manual_primary_source_normalization"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'skull-king:current:%'
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
  )
  SELECT
    'skull-king:current:binding:' || rn.rule_id,
    'skull-king:current:rule:' || rn.rule_id,
    CASE
      WHEN rn.source_locator LIKE 'skull-king:faq:%'
        THEN 'publisher:grandpa-becks:skull-king:current-rules-faq'
      ELSE 'publisher:grandpa-becks:skull-king:current-rulebook'
    END,
    rn.source_locator,
    'supports',
    '{"audit_date":"2026-08-31","method":"manual_primary_source_verification"}'::jsonb,
    '{"seed":"032_seed_skull_king_current_ruleset"}'::jsonb,
    now()
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'skull-king:current:%'
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
