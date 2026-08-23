BEGIN;

-- Disney Lorcana is a living trading card game, so the canonical RuleSet is
-- revision-bound rather than treated as a one-time static edition.
-- Japanese product identity and gameplay rules are bound to Takara Tomy's
-- official Japanese site and Comprehensive Rules v2.2.0 (effective 2026-07-10).
-- Card-set release notes, tournament policy, starter-product instructions,
-- fan summaries, and older rules revisions are deliberately excluded.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:takaratomy:lorcana:japanese-official',
    'https://www.takaratomy.co.jp/products/disneylorcana/',
    'Takara Tomy Disney Lorcana Trading Card Game official Japanese site',
    'publisher_product_page',
    'Takara Tomy / Ravensburger',
    'physical',
    'ja',
    'current',
    '{"authority":"publisher","role":"canonical_japanese_product_identity","audit_date":"2026-08-23","notes":"Official Japanese Disney Lorcana TCG site operated by Takara Tomy; gameplay rules remain revisioned separately","excludes":["fan summaries","digital implementations","tournament policy","individual set release notes"]}'::jsonb
  ),
  (
    'publisher:takaratomy:lorcana:cr-2.2.0-ja',
    'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=',
    'Disney Lorcana Comprehensive Rules Japanese v2.2.0',
    'publisher_rulebook',
    'Takara Tomy / Ravensburger',
    'physical',
    'ja',
    '2.2.0-effective-2026-07-10',
    '{"authority":"publisher","role":"gameplay_rules","audit_date":"2026-08-23","effective_date":"2026-07-10","living_document":true,"notes":"Current official Japanese Comprehensive Rules; future revisions must be represented explicitly rather than silently overwriting rule identity"}'::jsonb
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
  ('lorcana:product:jp-identity', 'publisher:takaratomy:lorcana:japanese-official', NULL, 'Disney Lorcana Trading Card Game', 'Official Japanese product and rules authority'),
  ('lorcana:cr-2.2.0:deck', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 11, '1.10.1 デッキ', 'Constructed deck: at least 60 cards, at most two ink types, at most four cards with the same full name, and no banned cards'),
  ('lorcana:cr-2.2.0:setup', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 13, '2.2 セットアップステージ', 'Randomly determine starting player, shuffle/cut decks, begin at 0 lore, draw seven cards'),
  ('lorcana:cr-2.2.0:mulligan', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 14, '2.2.2 最初の手札の入れ替え', 'Once per game, put any number of initial-hand cards on bottom, draw back to seven, then shuffle if cards were replaced'),
  ('lorcana:cr-2.2.0:win-loss', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 14, '2.3.3 ゲーム終了', '20 or more lore wins; ending a turn with zero cards in deck loses; multiplayer last remaining player wins; concession loses'),
  ('lorcana:cr-2.2.0:start-phase', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 15, '3.2 スタートフェイズ', 'Ready all own cards in play and inkwell, perform set step, then draw one card; starting player skips draw on the first turn'),
  ('lorcana:cr-2.2.0:main-actions', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 17, '4.1 ターン行動', 'During main phase, actions may be taken in any order: ink a card, play a card, use a card ability, quest, challenge, move a character to a location'),
  ('lorcana:cr-2.2.0:ink', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 17, '4.2 カードをインクにする', 'Reveal one hand card with an inkwell symbol and place it facedown ready in the inkwell; this turn action is once per turn'),
  ('lorcana:cr-2.2.0:quest', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 21, '4.5 クエストする', 'An eligible character quests by being exerted; its player gains lore equal to the character lore value'),
  ('lorcana:cr-2.2.0:challenge', 'publisher:takaratomy:lorcana:cr-2.2.0-ja', 22, '4.6 チャレンジする', 'Choose an eligible ready character and an opposing exerted character, exert the challenger, then deal challenge damage simultaneously according to strength and applicable modifiers')
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
  WHERE g.slug = 'disney-lorcana'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Disney Lorcana Game/Work row is required before applying RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://www.takaratomy.co.jp/products/disneylorcana/',
    source_url = 'https://www.takaratomy.co.jp/products/disneylorcana/',
    source_trust = 'official_publisher',
    edition_label = '日本語版 TCG',
    language_code = 'ja',
    publisher = 'Takara Tomy / Ravensburger',
    min_players = 2,
    max_players = NULL,
    source_revision = 'Disney Lorcana Comprehensive Rules 2.2.0 (effective 2026-07-10)',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = '日本語版 TCG'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = 'cr-2.2.0-ja-2026-07-10'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      effective_date, status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', '日本語版 TCG',
      'Disney Lorcana Comprehensive Rules 2.2.0 (effective 2026-07-10)',
      true, 'cr-2.2.0-ja-2026-07-10', 'physical', 'Takara Tomy / Ravensburger',
      DATE '2026-07-10', 'active', 'source_bound',
      ARRAY[
        'publisher:takaratomy:lorcana:japanese-official',
        'publisher:takaratomy:lorcana:cr-2.2.0-ja'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Disney Lorcana Comprehensive Rules 2.2.0 (effective 2026-07-10)',
      is_active = true,
      publisher_name = 'Takara Tomy / Ravensburger',
      effective_date = DATE '2026-07-10',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:takaratomy:lorcana:japanese-official',
        'publisher:takaratomy:lorcana:cr-2.2.0-ja'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'setup.constructed-deck', 'setup', '構築フォーマットではデッキを60枚以上とし、使用できるインク・タイプは2種類まで、同一のフルネームを持つカードは4枚までとし、禁止カードは入れられない。', 0, 'source_bound', 'lorcana:rule:setup.constructed-deck', 'lorcana:binding:setup.constructed-deck', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:deck', '{"scope":"constructed_format"}'::jsonb),
    (v_ruleset_id, 'setup.start-and-seven', 'setup', '開始プレイヤーをランダムに決め、各プレイヤーはデッキを十分に無作為化して対戦相手にシャッフルとカットの機会を与える。全員0ロアから開始し、最初の手札として7枚引く。', 1, 'source_bound', 'lorcana:rule:setup.start-and-seven', 'lorcana:binding:setup.start-and-seven', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:setup', '{}'::jsonb),
    (v_ruleset_id, 'setup.one-mulligan', 'setup', '各プレイヤーは各ゲームで1度だけ最初の手札を入れ替えられる。好きな枚数を公開せずデッキの一番下へ置き、手札が7枚になるまで引き、1枚以上入れ替えた場合はその後デッキをシャッフルする。', 2, 'source_bound', 'lorcana:rule:setup.one-mulligan', 'lorcana:binding:setup.one-mulligan', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:mulligan', '{}'::jsonb),
    (v_ruleset_id, 'turn.ready-set-draw', 'turn', 'スタートフェイズでは、自分の場とインクウェルのカードをすべてレディし、セットステップを処理してからカードを1枚引く。ただしゲーム最初のターンでは開始プレイヤーはドローステップを飛ばす。', 0, 'source_bound', 'lorcana:rule:turn.ready-set-draw', 'lorcana:binding:turn.ready-set-draw', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:start-phase', '{}'::jsonb),
    (v_ruleset_id, 'turn.main-actions', 'turn', 'メインフェイズでは任意の順序で、カードをインクにする、カードをプレイする、カードの能力を使用する、クエストする、チャレンジする、キャラクターをロケーションへ移動させる、の各ターン行動を行える。カードをインクにするターン行動を除き、通常は同じ種類のターン行動を何度でも行える。', 1, 'source_bound', 'lorcana:rule:turn.main-actions', 'lorcana:binding:turn.main-actions', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:main-actions', '{}'::jsonb),
    (v_ruleset_id, 'action.ink-once', 'action', 'カードをインクにするターン行動は1ターンに1度だけ行える。手札からインクウェル・シンボルを持つカード1枚を公開して確認した後、そのカードをインクウェルへレディかつ裏向きで置く。', 0, 'source_bound', 'lorcana:rule:action.ink-once', 'lorcana:binding:action.ink-once', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:ink', '{}'::jsonb),
    (v_ruleset_id, 'action.quest-for-lore', 'action', 'クエストできるキャラクターを宣言し、制限と必要なコストを確認した後、そのキャラクターをエグザートする。そのプレイヤーはクエストしたキャラクターのロア値と同じ数のロアを得る。', 1, 'source_bound', 'lorcana:rule:action.quest-for-lore', 'lorcana:binding:action.quest-for-lore', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:quest', '{}'::jsonb),
    (v_ruleset_id, 'action.challenge-exerted-character', 'action', 'チャレンジするには、条件を満たす自分のレディしているキャラクターを選び、通常はエグザートしている対戦相手のキャラクターを対象にして、チャレンジするキャラクターをエグザートする。チャレンジ・ダメージでは双方の攻撃力などを反映したダメージを計算し、キャラクター同士なら同時に与え合う。', 2, 'source_bound', 'lorcana:rule:action.challenge-exerted-character', 'lorcana:binding:action.challenge-exerted-character', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:challenge', '{"note":"locations follow additional challenge rules and are not collapsed into the character-target summary"}'::jsonb),
    (v_ruleset_id, 'victory.twenty-lore', 'victory', 'ロアを20以上持つプレイヤーはゲームに勝利する。', 0, 'source_bound', 'lorcana:rule:victory.twenty-lore', 'lorcana:binding:victory.twenty-lore', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:win-loss', '{}'::jsonb),
    (v_ruleset_id, 'game-end.empty-deck-loss', 'game_end', 'デッキが0枚でターンを終了したプレイヤーはゲームに敗北する。', 0, 'source_bound', 'lorcana:rule:game-end.empty-deck-loss', 'lorcana:binding:game-end.empty-deck-loss', 'https://www.takaratomy.co.jp/products/disneylorcana/common/pdf/Disney-Lorcana-Comprehensive-Rules_JP.pdf?20260710=', 'lorcana:cr-2.2.0:win-loss', '{"revision_sensitive":true}'::jsonb)
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
    'lorcana:rule:' || rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_source_normalization","audit_date":"2026-08-23","scope":"japanese_tcg_cr_2_2_0","living_rules":true}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id IN (
      'setup.constructed-deck','setup.start-and-seven','setup.one-mulligan',
      'turn.ready-set-draw','turn.main-actions','action.ink-once',
      'action.quest-for-lore','action.challenge-exerted-character',
      'victory.twenty-lore','game-end.empty-deck-loss'
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
    ('lorcana:binding:setup.constructed-deck','lorcana:rule:setup.constructed-deck','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:deck','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:setup.start-and-seven','lorcana:rule:setup.start-and-seven','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:setup','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:setup.one-mulligan','lorcana:rule:setup.one-mulligan','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:mulligan','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:turn.ready-set-draw','lorcana:rule:turn.ready-set-draw','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:start-phase','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:turn.main-actions','lorcana:rule:turn.main-actions','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:main-actions','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:action.ink-once','lorcana:rule:action.ink-once','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:ink','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:action.quest-for-lore','lorcana:rule:action.quest-for-lore','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:quest','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:action.challenge-exerted-character','lorcana:rule:action.challenge-exerted-character','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:challenge','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:victory.twenty-lore','lorcana:rule:victory.twenty-lore','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:win-loss','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('lorcana:binding:game-end.empty-deck-loss','lorcana:rule:game-end.empty-deck-loss','publisher:takaratomy:lorcana:cr-2.2.0-ja','lorcana:cr-2.2.0:win-loss','supports','{"review":"publisher_source","revision_sensitive":true}'::jsonb,'{}'::jsonb,now())
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
