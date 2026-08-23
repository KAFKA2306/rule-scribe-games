BEGIN;

-- Jaipur physical Japanese edition sold by Hobby Japan from 2020.
-- Product identity is bound to Hobby Japan's official Japanese product page.
-- Rule substance is normalized from SPACE Cowboys' official Jaipur rulebook for the
-- Vincent Dutrait new edition. The older GameWorks packaging, digital implementations,
-- community summaries, tournament variants, and unrelated 2-player titles are excluded.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:hobbyjapan:jaipur:2020-product',
    'https://hobbyjapan.games/jaipur/',
    'Hobby Japan ジャイプル 日本語版 official product page',
    'publisher_product_page',
    'Hobby Japan',
    'physical',
    'ja',
    '2020-09',
    '{"authority":"publisher","role":"canonical_japanese_product_identity","audit_date":"2026-08-23","notes":"2020 reprint changed box, artwork and JAN; page identifies SPACE Cowboys, Vincent Dutrait artwork, 55 cards and 60 tokens","excludes":["GameWorks legacy packaging","digital implementations","community summaries","variants"]}'::jsonb
  ),
  (
    'publisher:spacecowboys:jaipur:current-product',
    'https://www.spacecowboys-games.com/game/jaipur/',
    'SPACE Cowboys Jaipur official product page',
    'publisher_product_page',
    'SPACE Cowboys',
    'physical',
    'en',
    'vincent-dutrait-new-edition',
    '{"authority":"publisher","role":"canonical_new_edition_identity","audit_date":"2026-08-23"}'::jsonb
  ),
  (
    'publisher:spacecowboys:jaipur:2019-rulebook',
    'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf',
    'SPACE Cowboys Jaipur official rulebook ©2019',
    'publisher_rulebook',
    'SPACE Cowboys',
    'physical',
    'en',
    '2019-new-edition',
    '{"authority":"publisher","role":"canonical_base_rules","audit_date":"2026-08-23"}'::jsonb
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
  ('jaipur:product:jp-identity', 'publisher:hobbyjapan:jaipur:2020-product', NULL, 'ジャイプル', 'Japanese edition; SPACE Cowboys; Vincent Dutrait; 2 players; 30 minutes; age 12+; released 2020-09; 55 cards; 38 goods tokens; 18 bonus tokens; 1 camel token; 3 Seals of Excellence'),
  ('jaipur:rulebook:setup', 'publisher:spacecowboys:jaipur:2019-rulebook', 1, 'SETUP', 'Start market with 3 camels, deal 5 cards each, fill market to 5 with 2 deck cards, then move all camels from each hand to that player herd'),
  ('jaipur:rulebook:turn', 'publisher:spacecowboys:jaipur:2019-rulebook', 2, 'GAME TURN', 'On a turn choose either TAKE CARDS or SELL CARDS, never both'),
  ('jaipur:rulebook:take', 'publisher:spacecowboys:jaipur:2019-rulebook', 3, 'TAKE CARDS', 'Take one good, exchange several goods, or take all camels; hand limit is 7 goods cards'),
  ('jaipur:rulebook:sell', 'publisher:spacecowboys:jaipur:2019-rulebook', 4, 'SELL CARDS', 'Sell one goods type; receive highest-value available goods tokens; sales of 3+ gain a bonus; diamonds, gold and silver require at least 2 cards'),
  ('jaipur:rulebook:end', 'publisher:spacecowboys:jaipur:2019-rulebook', 5, 'END OF A ROUND / SCORING / END OF THE GAME', 'Round ends when 3 goods-token types are depleted or the deck cannot refill the market to 5; camel majority is 5 rupees; richest trader takes a Seal; first to 2 Seals wins'),
  ('jaipur:rulebook:reminders', 'publisher:spacecowboys:jaipur:2019-rulebook', 6, 'REMINDERS AND NOTES', 'Exchange requires 2+ cards; same goods type cannot be both taken and returned; camels do not count toward hand limit')
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
  WHERE g.slug = 'jaipur'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Jaipur Game/Work row is required before applying RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://hobbyjapan.games/jaipur/',
    source_url = 'https://hobbyjapan.games/jaipur/',
    source_trust = 'official_publisher',
    edition_label = 'ホビージャパン日本語版 (2020 SPACE Cowboys edition)',
    language_code = 'ja',
    publisher = 'SPACE Cowboys / Hobby Japan',
    source_revision = 'Hobby Japan 2020 Japanese product identity + SPACE Cowboys official 2019 new-edition rulebook',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'ホビージャパン日本語版 (2020 SPACE Cowboys edition)'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2020-space-cowboys-ja'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'ホビージャパン日本語版 (2020 SPACE Cowboys edition)',
      'Hobby Japan 2020 Japanese product identity + SPACE Cowboys official 2019 new-edition rulebook',
      true, '2020-space-cowboys-ja', 'physical', 'SPACE Cowboys / Hobby Japan',
      'active', 'source_bound',
      ARRAY[
        'publisher:hobbyjapan:jaipur:2020-product',
        'publisher:spacecowboys:jaipur:current-product',
        'publisher:spacecowboys:jaipur:2019-rulebook'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Hobby Japan 2020 Japanese product identity + SPACE Cowboys official 2019 new-edition rulebook',
      is_active = true,
      publisher_name = 'SPACE Cowboys / Hobby Japan',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:hobbyjapan:jaipur:2020-product',
        'publisher:spacecowboys:jaipur:current-product',
        'publisher:spacecowboys:jaipur:2019-rulebook'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'setup.market-and-hands', 'setup', '市場には最初にラクダ3枚を表向きで置く。残りのカードを混ぜて各プレイヤーへ5枚ずつ配り、山札から2枚を市場へ追加して5枚にする。その後、各プレイヤーは手札にあるラクダをすべて自分の群れへ移す。ラクダを移した後に手札を5枚へ補充はしない。', 0, 'source_bound', 'jaipur:rule:setup.market-and-hands', 'jaipur:binding:setup.market-and-hands', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:setup', '{}'::jsonb),
    (v_ruleset_id, 'turn.take-or-sell', 'turn', '自分の手番では「カードを取る」か「カードを売る」のどちらか一方だけを行う。同じ手番で両方は行えない。', 0, 'source_bound', 'jaipur:rule:turn.take-or-sell', 'jaipur:binding:turn.take-or-sell', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:turn', '{}'::jsonb),
    (v_ruleset_id, 'take.single-good', 'action', '市場から商品カード1枚だけを取る場合、そのカードを手札へ加え、山札の一番上のカード1枚で市場を補充する。', 0, 'source_bound', 'jaipur:rule:take.single-good', 'jaipur:binding:take.single-good', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:take', '{}'::jsonb),
    (v_ruleset_id, 'take.exchange', 'action', '交換では市場から2枚以上の商品カードを取り、同じ枚数の手札の商品カード・群れのラクダ、またはその組合せを市場へ戻す。1枚対1枚の交換はできず、同じ種類の商品を市場から取りながら同時に市場へ戻すこともできない。', 1, 'source_bound', 'jaipur:rule:take.exchange', 'jaipur:binding:take.exchange', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:reminders', '{}'::jsonb),
    (v_ruleset_id, 'take.all-camels', 'action', '市場のラクダを取る場合は、そこにあるラクダをすべて自分の群れへ加え、その後、山札から市場が5枚になるまで補充する。', 2, 'source_bound', 'jaipur:rule:take.all-camels', 'jaipur:binding:take.all-camels', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:take', '{}'::jsonb),
    (v_ruleset_id, 'hand.limit-seven', 'condition', '手番終了時に手札の商品カードは7枚を超えてはならない。群れのラクダはこの7枚制限に数えない。', 0, 'source_bound', 'jaipur:rule:hand.limit-seven', 'jaipur:binding:hand.limit-seven', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:reminders', '{}'::jsonb),
    (v_ruleset_id, 'sell.goods-and-bonus', 'action', '商品を売るときは1種類だけを選び、任意の枚数を捨て札にする。売った枚数と同数の対応商品トークンを価値の高いものから受け取り、3枚以上を一度に売れば枚数に対応するボーナストークンも1枚得る。ダイヤモンド・金・銀を売る場合は最低2枚必要。', 0, 'source_bound', 'jaipur:rule:sell.goods-and-bonus', 'jaipur:binding:sell.goods-and-bonus', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:sell', '{}'::jsonb),
    (v_ruleset_id, 'round-end.market-or-tokens', 'game_end', 'ラウンドは、6種類の商品トークンのうち3種類の山がなくなった場合、または山札のカードが足りず市場を5枚まで補充できない場合にただちに終了する。', 0, 'source_bound', 'jaipur:rule:round-end.market-or-tokens', 'jaipur:binding:round-end.market-or-tokens', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:end', '{}'::jsonb),
    (v_ruleset_id, 'scoring.camel-majority', 'scoring', 'ラウンド終了時、群れのラクダが最も多いプレイヤーは5ルピーのラクダトークンを得る。ラクダ数が同じなら、どちらもラクダトークンを得ない。', 0, 'source_bound', 'jaipur:rule:scoring.camel-majority', 'jaipur:binding:scoring.camel-majority', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:end', '{}'::jsonb),
    (v_ruleset_id, 'scoring.round-winner', 'scoring', '各自が獲得トークンのルピーを合計し、最も裕福なプレイヤーが優秀の証を1枚得る。同点ならボーナストークンが多い方、それも同数なら商品トークンが多い方が優秀の証を得る。', 1, 'source_bound', 'jaipur:rule:scoring.round-winner', 'jaipur:binding:scoring.round-winner', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:end', '{}'::jsonb),
    (v_ruleset_id, 'victory.two-seals', 'victory', '先に優秀の証を2枚獲得したプレイヤーがゲームに勝つ。どちらも2枚に達していない場合は次のラウンドを準備し、直前のラウンドで負けたプレイヤーが先手になる。', 0, 'source_bound', 'jaipur:rule:victory.two-seals', 'jaipur:binding:victory.two-seals', 'https://cdn.svc.asmodee.net/production-spacecowboys/uploads/2025/11/Rules-JAIPUR-12x17-Version-EN_BD.pdf', 'jaipur:rulebook:end', '{}'::jsonb)
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
    'jaipur:rule:' || rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_source_normalization","audit_date":"2026-08-23"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id IN (
      'setup.market-and-hands','turn.take-or-sell','take.single-good','take.exchange',
      'take.all-camels','hand.limit-seven','sell.goods-and-bonus',
      'round-end.market-or-tokens','scoring.camel-majority','scoring.round-winner','victory.two-seals'
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
    ('jaipur:binding:setup.market-and-hands','jaipur:rule:setup.market-and-hands','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:setup','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:turn.take-or-sell','jaipur:rule:turn.take-or-sell','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:turn','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:take.single-good','jaipur:rule:take.single-good','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:take','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:take.exchange','jaipur:rule:take.exchange','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:reminders','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:take.all-camels','jaipur:rule:take.all-camels','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:take','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:hand.limit-seven','jaipur:rule:hand.limit-seven','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:reminders','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:sell.goods-and-bonus','jaipur:rule:sell.goods-and-bonus','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:sell','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:round-end.market-or-tokens','jaipur:rule:round-end.market-or-tokens','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:scoring.camel-majority','jaipur:rule:scoring.camel-majority','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:scoring.round-winner','jaipur:rule:scoring.round-winner','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('jaipur:binding:victory.two-seals','jaipur:rule:victory.two-seals','publisher:spacecowboys:jaipur:2019-rulebook','jaipur:rulebook:end','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now())
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
