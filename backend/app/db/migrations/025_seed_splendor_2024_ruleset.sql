BEGIN;

-- Splendor 2024 refreshed physical edition, bound to first-party evidence.
--
-- Source policy:
--   * Hobby Japan product page is canonical for the Japanese 2024 revised
--     product identity and separates it from the 2015 old edition.
--   * SPACE Cowboys / Asmodee 2024 refreshed rulebook is canonical for the
--     base-game rules normalized below.
--   * Splendor Duel, expansions, tournament rules and the 2015 edition are
--     intentionally excluded from this RuleSet.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:hobbyjapan:splendor:2024-revised-product',
    'https://hobbyjapan.games/splendor/',
    'Hobby Japan Splendor revised Japanese product page',
    'publisher_product_page',
    'Hobby Japan / SPACE Cowboys',
    'physical',
    'ja',
    '2024-07',
    '{"authority":"publisher_localization","role":"canonical_japanese_2024_product_identity","audit_date":"2026-08-22","excludes":["2015 old edition","Splendor Duel","expansions"]}'::jsonb
  ),
  (
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
    'SPACE Cowboys Splendor refreshed 2024 rulebook',
    'publisher_rulebook',
    'SPACE Cowboys',
    'physical',
    'es',
    '2024-refresh',
    '{"authority":"publisher","role":"canonical_base_rules_for_2024_refresh","audit_date":"2026-08-22","copyright_year":2024}'::jsonb
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
  locator_id, source_id, section_heading, external_reference
)
VALUES
  (
    'splendor:hj:identity',
    'publisher:hobbyjapan:splendor:2024-revised-product',
    '宝石の煌き',
    '改訂版; SPACE Cowboys; 2024年7月; 40 gem tokens; 90 development cards; 10 noble tiles; old 2015 edition explicitly separated'
  ),
  (
    'splendor:rulebook:setup',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'PREPARACIÓN',
    '4-player setup plus 2/3-player adjustments'
  ),
  (
    'splendor:rulebook:actions',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'Acciones',
    'exactly one of four actions; gem-taking, reserving, purchasing'
  ),
  (
    'splendor:rulebook:bonuses',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'Bonificaciones',
    'development-card bonuses discount future purchases'
  ),
  (
    'splendor:rulebook:replenish',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'Reponer cartas',
    'replace face-up development cards after purchase or reserve while deck remains'
  ),
  (
    'splendor:rulebook:token-limit',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'Límite de la reserva de fichas',
    'maximum 10 tokens at end of turn'
  ),
  (
    'splendor:rulebook:nobles',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'LOSETAS DE NOBLE',
    'end-of-turn noble acquisition; at most one noble per turn'
  ),
  (
    'splendor:rulebook:end',
    'publisher:space-cowboys:splendor:2024-refresh-rulebook',
    'FINAL DE LA PARTIDA',
    '15+ prestige trigger; equal turns; most prestige; fewest development cards tiebreak; shared win if still tied'
  )
ON CONFLICT (locator_id) DO UPDATE SET
  source_id = EXCLUDED.source_id,
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
  WHERE g.slug = 'splendor'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Splendor Game/Work row is required before applying the 2024 RuleSet seed';
  END IF;

  -- Repository-backed identity binding. This intentionally does not rewrite
  -- legacy rules_content; the player-facing cutover happens only after the
  -- canonical presentation is verified against production Before state.
  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://hobbyjapan.games/splendor/',
    source_url = 'https://hobbyjapan.games/splendor/',
    source_trust = 'official_publisher',
    edition_label = 'ホビージャパン日本語版 改訂版 (2024)',
    language_code = 'ja',
    publisher = 'SPACE Cowboys / ホビージャパン',
    source_revision = '2024 revised Japanese product / SPACE Cowboys 2024 refreshed base rules',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'ホビージャパン日本語版 改訂版 (2024)'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2024-refresh'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'ホビージャパン日本語版 改訂版 (2024)',
      'Hobby Japan 2024 revised Japanese product + SPACE Cowboys 2024 refreshed base rulebook',
      true, '2024-refresh', 'physical', 'SPACE Cowboys / ホビージャパン',
      'active', 'source_bound',
      ARRAY[
        'publisher:hobbyjapan:splendor:2024-revised-product',
        'publisher:space-cowboys:splendor:2024-refresh-rulebook'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Hobby Japan 2024 revised Japanese product + SPACE Cowboys 2024 refreshed base rulebook',
      is_active = true,
      publisher_name = 'SPACE Cowboys / ホビージャパン',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:hobbyjapan:splendor:2024-revised-product',
        'publisher:space-cowboys:splendor:2024-refresh-rulebook'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (
      v_ruleset_id, 'setup.market', 'setup',
      '発展カードをレベル別にシャッフルし、各レベルを4枚ずつ表向きにする。4人戦では貴族タイルを5枚公開し、宝石・黄金トークンを色別の共有サプライに置く。',
      0, 'source_bound', 'splendor:2024:rule:setup.market', 'splendor:2024:binding:setup.market',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:setup', '{"scope":"4-player base setup"}'::jsonb
    ),
    (
      v_ruleset_id, 'setup.player-count', 'setup',
      '3人戦では貴族4枚・各色の宝石5枚、2人戦では貴族3枚・各色の宝石4枚を使用する。黄金トークンは減らさない。',
      1, 'source_bound', 'splendor:2024:rule:setup.player-count', 'splendor:2024:binding:setup.player-count',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:setup', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'turn.one-action', 'turn',
      '自分のターンには、定められた4種類のアクションのうち1つだけを実行する。',
      0, 'source_bound', 'splendor:2024:rule:turn.one-action', 'splendor:2024:binding:turn.one-action',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:actions', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'action.take-three-different', 'action',
      '異なる3色の宝石トークンを1枚ずつ取る。3色取れない場合は異なる2色または1色だけ取れる。このアクションでは黄金トークンを取れない。',
      1, 'source_bound', 'splendor:2024:rule:action.take-three-different', 'splendor:2024:binding:action.take-three-different',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:actions', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'action.take-two-same', 'action',
      '同じ色の宝石トークンを2枚取る。このアクションは、取る前にその色が共有サプライに4枚以上ある場合だけ実行でき、黄金トークンは対象にできない。',
      2, 'source_bound', 'splendor:2024:rule:action.take-two-same', 'splendor:2024:binding:action.take-two-same',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:actions', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'action.reserve', 'action',
      '表向きの発展カード1枚、または任意のレベルの山札の一番上1枚を非公開で予約し、黄金トークンが残っていれば1枚取る。予約カードは同時に3枚まで保持できる。',
      3, 'source_bound', 'splendor:2024:rule:action.reserve', 'splendor:2024:binding:action.reserve',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:actions', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'action.purchase', 'action',
      '表向きの発展カード1枚または自分が予約したカード1枚を、必要コストを支払って獲得する。黄金トークンは任意の宝石色の代用として使える。',
      4, 'source_bound', 'splendor:2024:rule:action.purchase', 'splendor:2024:binding:action.purchase',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:actions', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'effect.development-bonus', 'effect',
      '獲得した発展カードのボーナスは、以後その色のカード購入コストをボーナス1つにつき宝石1個分減らす。',
      0, 'source_bound', 'splendor:2024:rule:effect.development-bonus', 'splendor:2024:binding:effect.development-bonus',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:bonuses', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'effect.replenish-market', 'effect',
      '表向きの発展カードを獲得または予約したら、対応するレベルの山札が残っている限り補充し、各レベル4枚の表向きカードを維持する。',
      1, 'source_bound', 'splendor:2024:rule:effect.replenish-market', 'splendor:2024:binding:effect.replenish-market',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:replenish', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'limit.tokens', 'condition',
      'ターン終了時に11枚以上のトークンを持っている場合、自分で選んで共有サプライへ戻し、10枚にする。',
      0, 'source_bound', 'splendor:2024:rule:limit.tokens', 'splendor:2024:binding:limit.tokens',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:token-limit', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'effect.noble', 'effect',
      'ターン終了時に貴族の条件を満たしていれば貴族タイル1枚を獲得する。これはアクションではなく、1ターンに獲得できる貴族は1枚まで。',
      2, 'source_bound', 'splendor:2024:rule:effect.noble', 'splendor:2024:binding:effect.noble',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:nobles', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'game-end.trigger', 'game_end',
      'ターン終了時に威信ポイントが15点以上になったプレイヤーが出るとゲーム終了が発動し、全員の手番数が同じになるまで続ける。',
      0, 'source_bound', 'splendor:2024:rule:game-end.trigger', 'splendor:2024:binding:game-end.trigger',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:end', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'victory.most-prestige', 'victory',
      'ゲーム終了時に威信ポイントが最も高いプレイヤーが勝者となる。',
      0, 'source_bound', 'splendor:2024:rule:victory.most-prestige', 'splendor:2024:binding:victory.most-prestige',
      'https://hobbyjapan.games/splendor/',
      'splendor:hj:identity', '{}'::jsonb
    ),
    (
      v_ruleset_id, 'victory.tie-break', 'victory',
      '威信ポイントが同点なら、獲得した発展カードがより少ない同点プレイヤーが勝つ。それでも同点なら勝利を共有する。',
      1, 'source_bound', 'splendor:2024:rule:victory.tie-break', 'splendor:2024:binding:victory.tie-break',
      'https://cdn.svc.asmodee.net/production-asmodeees/uploads/2024/06/SCSPL01ES_SPLENDOR_Rules_HD-PRINT_20240220.pdf',
      'splendor:rulebook:end', '{}'::jsonb
    )
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
    'splendor:2024:rule:' || rn.rule_id,
    v_ruleset_id,
    'rule_statement',
    jsonb_build_object('statement', rn.normalized_statement, 'source_scope', 'Splendor 2024 refreshed base physical rules'),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"seed":"025_seed_splendor_2024_ruleset","audit_date":"2026-08-22","method":"manual_primary_source_normalization"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'splendor:2024:%'
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
    'splendor:2024:binding:' || rn.rule_id,
    'splendor:2024:rule:' || rn.rule_id,
    CASE WHEN rn.rule_id = 'victory.most-prestige'
      THEN 'publisher:hobbyjapan:splendor:2024-revised-product'
      ELSE 'publisher:space-cowboys:splendor:2024-refresh-rulebook'
    END,
    rn.source_locator,
    'supports',
    '{"audit_date":"2026-08-22","method":"manual_primary_source_verification"}'::jsonb,
    '{"seed":"025_seed_splendor_2024_ruleset"}'::jsonb,
    now()
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.source_claim_ref LIKE 'splendor:2024:%'
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
