BEGIN;

-- Bind the catalog row to SUSABI GAMES' base HacKClaD product only.
-- CROSS FATE, DeltA, Portable Edition, tournament regulations, and fan material
-- are intentionally excluded. This migration also removes legacy content that
-- belonged to a different game sharing a similar title.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:susabi:hackclad:official-home',
    'https://www.hackclad.jp/home',
    'HacKClaD official website - HOME',
    'publisher_product_page',
    'SUSABI GAMES',
    'physical',
    'ja',
    'current-base-game',
    '{"authority":"publisher","role":"base_game_identity_and_overview","audit_date":"2026-08-23","excludes":["HacKClaD CROSS FATE","HacKClaD.DeltA","HacKClaD -Portable Edition-","tournament regulations","fan summaries"]}'::jsonb
  ),
  (
    'publisher:susabi:hackclad:official-game',
    'https://www.hackclad.jp/game',
    'HacKClaD official website - GAME',
    'publisher_rules_support_page',
    'SUSABI GAMES',
    'physical',
    'ja',
    'current-base-game',
    '{"authority":"publisher","role":"base_game_system_overview","audit_date":"2026-08-23"}'::jsonb
  ),
  (
    'publisher:susabi:hackclad:official-faq',
    'https://www.hackclad.jp/FAQ',
    'HacKClaD official website - FAQ',
    'publisher_rules_faq',
    'SUSABI GAMES',
    'physical',
    'ja',
    'current-base-game-faq',
    '{"authority":"publisher","role":"base_rule_clarifications","audit_date":"2026-08-23","notes":"Only FAQ entries stated as basic HacKClaD rules are bound here; expansion-specific questions are excluded"}'::jsonb
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
  ('hackclad:home:product-info','publisher:susabi:hackclad:official-home','製品情報','Base HacKClaD: deck-building strategy SLG, 1-4 players, 90-120 minutes'),
  ('hackclad:home:deck-growth','publisher:susabi:hackclad:official-home','ゲームシステム紹介','Character-specific skill-card decks can be strengthened as the game progresses'),
  ('hackclad:game:overview','publisher:susabi:hackclad:official-game','GAME','Fight the Clad, compete for fame, and gain magic stones by planning actions around predicted Clad behavior'),
  ('hackclad:faq:moving-attack-reaction','publisher:susabi:hackclad:official-faq','①基本ルールに関するFAQ','Q: 「移動攻撃」に対して対応アクションを行うことは可能ですか？'),
  ('hackclad:faq:damage-vp','publisher:susabi:hackclad:official-faq','①基本ルールに関するFAQ','Q: スキルカード以外でクラッドにダメージを与えた場合にも魔石を獲得しますか？'),
  ('hackclad:faq:skill-no-target','publisher:susabi:hackclad:official-faq','①基本ルールに関するFAQ','Q: スキルカードの効果が作用する対象が無い場合、そのスキルカードを使用することができますか？'),
  ('hackclad:faq:injury-ends-turn','publisher:susabi:hackclad:official-faq','①基本ルールに関するFAQ','Q: プレイヤーが自分の手番中に負傷した場合、負傷後もスキルカードの使用やアクションを実行することができますか？')
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
  SELECT g.id, g.work_id INTO v_game_id, v_work_id
  FROM public.games g
  WHERE g.slug = 'hack-clad'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical HacKClaD Game/Work row is required before applying RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    title = 'HacKClaD',
    title_ja = 'HacKClaD',
    title_en = 'HacKClaD',
    description = 'フィールドを暴れまわる怪物「クラッド」と戦い、名声を競うデッキ構築型戦略シミュレーションゲーム。',
    summary = '予知されたクラッドの行動に合わせてアクションを組み立て、魔石を獲得しながらキャラクター固有のスキルデッキを成長させる。',
    rules = NULL,
    rules_content = NULL,
    structured_data = '{}'::jsonb,
    setup_summary = NULL,
    gameplay_summary = NULL,
    end_game_summary = NULL,
    identity_status = 'verified',
    identity_source = 'https://www.hackclad.jp/home',
    source_url = 'https://www.hackclad.jp/home',
    official_url = 'https://www.hackclad.jp/home',
    source_trust = 'official_publisher',
    content_review_status = 'review_required',
    is_official = true,
    edition_label = '基本セット HacKClaD（通常版）',
    language_code = 'ja',
    publisher = 'SUSABI GAMES',
    source_revision = 'HacKClaD official website + base-rules FAQ (audited 2026-08-23)',
    min_players = 1,
    max_players = 4,
    play_time = 120,
    published_year = NULL,
    bgg_url = NULL,
    amazon_url = NULL,
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = '基本セット HacKClaD（通常版）'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = 'base-official-web-2026-08-23'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', '基本セット HacKClaD（通常版）',
      'HacKClaD official website + base-rules FAQ (audited 2026-08-23)',
      true, 'base-official-web-2026-08-23', 'physical', 'SUSABI GAMES',
      'active', 'source_bound',
      ARRAY[
        'publisher:susabi:hackclad:official-home',
        'publisher:susabi:hackclad:official-game',
        'publisher:susabi:hackclad:official-faq'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'HacKClaD official website + base-rules FAQ (audited 2026-08-23)',
      is_active = true,
      publisher_name = 'SUSABI GAMES',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:susabi:hackclad:official-home',
        'publisher:susabi:hackclad:official-game',
        'publisher:susabi:hackclad:official-faq'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id,'game.goal','overview','プレイヤーはフィールドを暴れまわるクラッドと戦い、名声を競いながら、予知されたクラッドの行動に合わせてアクションを組み立てて魔石を獲得する。',0,'source_bound','hackclad:rule:game.goal','hackclad:binding:game.goal','https://www.hackclad.jp/game','hackclad:game:overview','{}'::jsonb),
    (v_ruleset_id,'progression.skill-deck-growth','progression','キャラクター固有のスキルカードデッキはゲーム進行に伴って強化でき、戦況に合わせて必要なスキルを選んでデッキを成長させる。',0,'source_bound','hackclad:rule:progression.skill-deck-growth','hackclad:binding:progression.skill-deck-growth','https://www.hackclad.jp/home','hackclad:home:deck-growth','{}'::jsonb),
    (v_ruleset_id,'reaction.moving-attack','reaction','クラッドの「移動攻撃」に対して対応アクションを実行できる。この場合、ダメージ軽減の効果は無効だが、それ以外の効果は発揮される。',0,'source_bound','hackclad:rule:reaction.moving-attack','hackclad:binding:reaction.moving-attack','https://www.hackclad.jp/FAQ','hackclad:faq:moving-attack-reaction','{}'::jsonb),
    (v_ruleset_id,'scoring.damage-magic-stones','scoring','プレイヤーが何らかの方法でクラッドにダメージを与えた場合、与えたダメージに等しいVP分の魔石を獲得する。',0,'source_bound','hackclad:rule:scoring.damage-magic-stones','hackclad:binding:scoring.damage-magic-stones','https://www.hackclad.jp/FAQ','hackclad:faq:damage-vp','{}'::jsonb),
    (v_ruleset_id,'action.skill-without-target','action','スキルカードは必要なコストと追加コストを支払い、使用条件を満たせば、効果を作用させる対象がなくても使用できる。処理できない部分は無視し、処理できる内容だけを処理する。',0,'source_bound','hackclad:rule:action.skill-without-target','hackclad:binding:action.skill-without-target','https://www.hackclad.jp/FAQ','hackclad:faq:skill-no-target','{}'::jsonb),
    (v_ruleset_id,'turn.injury-ends-turn','turn','手番プレイヤーが自分の手番中に負傷した場合、その手番は自動的に終了し、負傷後にスキルカード使用やアクションを続けることはできない。',0,'source_bound','hackclad:rule:turn.injury-ends-turn','hackclad:binding:turn.injury-ends-turn','https://www.hackclad.jp/FAQ','hackclad:faq:injury-ends-turn','{}'::jsonb),
    (v_ruleset_id,'metadata.player-count-time','metadata','基本セット HacKClaD（通常版）は1～4人用で、プレイ時間は90～120分。',0,'source_bound','hackclad:rule:metadata.player-count-time','hackclad:binding:metadata.player-count-time','https://www.hackclad.jp/home','hackclad:home:product-info','{}'::jsonb)
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
    'hackclad:rule:' || rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_source_normalization","audit_date":"2026-08-23","scope":"base_hackclad_only","excluded_material":["CROSS FATE","DeltA","Portable Edition","tournament regulations","fan summaries"]}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id IN (
      'game.goal','progression.skill-deck-growth','reaction.moving-attack',
      'scoring.damage-magic-stones','action.skill-without-target',
      'turn.injury-ends-turn','metadata.player-count-time'
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
    ('hackclad:binding:game.goal','hackclad:rule:game.goal','publisher:susabi:hackclad:official-game','hackclad:game:overview','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('hackclad:binding:progression.skill-deck-growth','hackclad:rule:progression.skill-deck-growth','publisher:susabi:hackclad:official-home','hackclad:home:deck-growth','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('hackclad:binding:reaction.moving-attack','hackclad:rule:reaction.moving-attack','publisher:susabi:hackclad:official-faq','hackclad:faq:moving-attack-reaction','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('hackclad:binding:scoring.damage-magic-stones','hackclad:rule:scoring.damage-magic-stones','publisher:susabi:hackclad:official-faq','hackclad:faq:damage-vp','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('hackclad:binding:action.skill-without-target','hackclad:rule:action.skill-without-target','publisher:susabi:hackclad:official-faq','hackclad:faq:skill-no-target','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('hackclad:binding:turn.injury-ends-turn','hackclad:rule:turn.injury-ends-turn','publisher:susabi:hackclad:official-faq','hackclad:faq:injury-ends-turn','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('hackclad:binding:metadata.player-count-time','hackclad:rule:metadata.player-count-time','publisher:susabi:hackclad:official-home','hackclad:home:product-info','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now())
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
