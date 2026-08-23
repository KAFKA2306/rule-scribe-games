BEGIN;

-- Dune: Imperium – Uprising stand-alone physical rules.
-- Identity is bound to Dire Wolf's official Uprising product/resources pages.
-- Rule substance is normalized from the official Uprising main rulebook and
-- publisher design notes for Uprising-specific mechanics. The CHOAM module,
-- six-player mode, Rise of Ix, Immortality, Bloodlines, digital challenges,
-- and other variants/expansions are not folded into the base RuleSet.

INSERT INTO public.evidence_sources (
  source_id, url, document_identity, source_type, publisher_name, platform,
  language_code, revision_label, trust_metadata
)
VALUES
  (
    'publisher:direwolf:dune-uprising:product',
    'https://www.direwolfdigital.com/dune-imperium-uprising/',
    'Dire Wolf Dune: Imperium – Uprising official product page',
    'publisher_product_page',
    'Dire Wolf Digital',
    'physical',
    'en',
    'current',
    '{"authority":"publisher","role":"canonical_standalone_product_identity","audit_date":"2026-08-22","excludes":["Dune: Imperium base game","Rise of Ix","Immortality","Bloodlines","six-player supplement","digital implementation"]}'::jsonb
  ),
  (
    'publisher:direwolf:dune-uprising:resources',
    'https://www.direwolfdigital.com/dune-imperium/resources/',
    'Dire Wolf Dune: Imperium official resources page',
    'publisher_resources_page',
    'Dire Wolf Digital',
    'physical',
    'ja',
    'current',
    '{"authority":"publisher","role":"japanese_uprising_rules_and_arclight_support_listing","audit_date":"2026-08-22"}'::jsonb
  ),
  (
    'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12',
    'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf',
    'Dune: Imperium – Uprising Main Rulebook 2023-10-12',
    'publisher_rulebook',
    'Dire Wolf Digital',
    'physical',
    'en',
    '2023-10-12',
    '{"authority":"publisher","role":"canonical_base_rules","audit_date":"2026-08-22"}'::jsonb
  ),
  (
    'publisher:direwolf:dune-uprising:spies-design-note',
    'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-3-spies/',
    'Dire Wolf Uprising Design Diary 3: Spies',
    'publisher_design_note',
    'Dire Wolf Digital',
    'physical',
    'en',
    '2023-09-13',
    '{"authority":"publisher","role":"uprising_spy_mechanic_clarification","audit_date":"2026-08-22"}'::jsonb
  ),
  (
    'publisher:direwolf:dune-uprising:sandworms-design-note',
    'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-2-sandworms-conflicts-and-the-shield-wall/',
    'Dire Wolf Uprising Design Diary 2: Sandworms, Conflicts, and the Shield Wall',
    'publisher_design_note',
    'Dire Wolf Digital',
    'physical',
    'en',
    '2023-08-25',
    '{"authority":"publisher","role":"uprising_sandworm_and_battle_icon_clarification","audit_date":"2026-08-22"}'::jsonb
  ),
  (
    'publisher:direwolf:dune-uprising:contracts-design-note',
    'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-4-contracts/',
    'Dire Wolf Uprising Design Diary 4: Contracts',
    'publisher_design_note',
    'Dire Wolf Digital',
    'physical',
    'en',
    '2023-10-04',
    '{"authority":"publisher","role":"choam_module_boundary","audit_date":"2026-08-22"}'::jsonb
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
  ('dune-uprising:product:identity', 'publisher:direwolf:dune-uprising:product', 'Long live the fighters!', 'Uprising is a stand-alone expansion/product with spies, contracts, sandworms, and an optional six-player mode'),
  ('dune-uprising:resources:jp', 'publisher:direwolf:dune-uprising:resources', '日本 (Japanese) Language Support', '[JP] Uprising Rules are listed; Japanese support partner is Arclight Games'),
  ('dune-uprising:rulebook:overview', 'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12', 'GAME OVERVIEW AND MAJOR CONCEPTS', '10-card starting deck; two starting Agents; 10+ VP/end-of-round or empty Conflict Deck end condition'),
  ('dune-uprising:rulebook:round-structure', 'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12', 'ROUND STRUCTURE', 'Round Start, Player Turns, Combat, Makers, Recall'),
  ('dune-uprising:rulebook:player-turns', 'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12', 'PHASE 2: PLAYER TURNS', 'Agent Turn or Reveal Turn; Reveal ends that player participation for the phase'),
  ('dune-uprising:spies:basics', 'publisher:direwolf:dune-uprising:spies-design-note', 'Spies', 'place spies on observation posts; recall for Infiltrate or Gather Intelligence'),
  ('dune-uprising:sandworms:basics', 'publisher:direwolf:dune-uprising:sandworms-design-note', 'Sandworms, Conflicts, and the Shield Wall', 'sandworms have strength 3, enter Conflict directly, never garrison, and double earned Conflict rewards'),
  ('dune-uprising:battle-icons:basics', 'publisher:direwolf:dune-uprising:sandworms-design-note', 'Rising Conflict', 'first-place winner takes Conflict card; matching two battle icons scores a Victory Point'),
  ('dune-uprising:choam:boundary', 'publisher:direwolf:dune-uprising:contracts-design-note', 'Contracts', 'CHOAM contracts are a modular optional element; without the module a contract icon gives 2 Solari')
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
  WHERE g.slug = 'dune-imperium-uprising'
  LIMIT 1;

  IF v_game_id IS NULL OR v_work_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Dune: Imperium – Uprising Game/Work row is required before applying RuleSet seed';
  END IF;

  UPDATE public.games
  SET
    identity_status = 'verified',
    identity_source = 'https://www.direwolfdigital.com/dune-imperium/resources/',
    source_url = 'https://www.direwolfdigital.com/dune-imperium-uprising/',
    source_trust = 'official_publisher',
    edition_label = 'Dune: Imperium – Uprising standalone physical (2023)',
    language_code = 'ja',
    publisher = 'Dire Wolf Digital / Arclight Games',
    source_revision = 'Dire Wolf Uprising main rulebook 2023-10-12; Japanese Uprising rules listed by publisher',
    updated_at = now()
  WHERE id = v_game_id;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id = v_game_id
    AND COALESCE(rs.language_code, '') = 'ja'
    AND COALESCE(rs.edition_label, '') = 'Dune: Imperium – Uprising standalone physical (2023)'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = '2023-10-12'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    INSERT INTO public.rule_sets (
      game_id, work_id, version, schema_version, language_code, edition_label,
      source_revision, is_active, revision_label, platform, publisher_name,
      status, verification_status, source_ids
    ) VALUES (
      v_game_id, v_work_id, 1, '1.0', 'ja', 'Dune: Imperium – Uprising standalone physical (2023)',
      'Dire Wolf Uprising main rulebook 2023-10-12 + official Japanese resource listing',
      true, '2023-10-12', 'physical', 'Dire Wolf Digital / Arclight Games',
      'active', 'source_bound',
      ARRAY[
        'publisher:direwolf:dune-uprising:product',
        'publisher:direwolf:dune-uprising:resources',
        'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12',
        'publisher:direwolf:dune-uprising:spies-design-note',
        'publisher:direwolf:dune-uprising:sandworms-design-note',
        'publisher:direwolf:dune-uprising:contracts-design-note'
      ]::text[]
    ) RETURNING id INTO v_ruleset_id;
  ELSE
    UPDATE public.rule_sets SET
      work_id = v_work_id,
      schema_version = '1.0',
      source_revision = 'Dire Wolf Uprising main rulebook 2023-10-12 + official Japanese resource listing',
      is_active = true,
      publisher_name = 'Dire Wolf Digital / Arclight Games',
      status = 'active',
      verification_status = 'source_bound',
      source_ids = ARRAY[
        'publisher:direwolf:dune-uprising:product',
        'publisher:direwolf:dune-uprising:resources',
        'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12',
        'publisher:direwolf:dune-uprising:spies-design-note',
        'publisher:direwolf:dune-uprising:sandworms-design-note',
        'publisher:direwolf:dune-uprising:contracts-design-note'
      ]::text[],
      updated_at = now()
    WHERE id = v_ruleset_id;
  END IF;

  INSERT INTO public.rule_nodes (
    rule_set_id, rule_id, node_type, normalized_statement, sequence,
    verification_status, source_claim_ref, evidence_ref,
    source_url, source_locator, metadata
  ) VALUES
    (v_ruleset_id, 'setup.deck-and-agents', 'setup', '各プレイヤーは同一構成の10枚の初期デッキで開始し、エージェント2体を持って開始する。ゲーム中に3体目のエージェントを得ることがある。', 0, 'source_bound', 'dune-uprising:rule:setup.deck-and-agents', 'dune-uprising:binding:setup.deck-and-agents', 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf', 'dune-uprising:rulebook:overview', '{}'::jsonb),
    (v_ruleset_id, 'round.structure', 'phase', '各ラウンドは、ラウンド開始、プレイヤー手番、戦闘、メイカー、回収の5フェイズをこの順で行う。', 0, 'source_bound', 'dune-uprising:rule:round.structure', 'dune-uprising:binding:round.structure', 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf', 'dune-uprising:rulebook:round-structure', '{}'::jsonb),
    (v_ruleset_id, 'round.start', 'phase', 'ラウンド開始時に新しい紛争カードを公開し、その後各プレイヤーは自分のデッキから5枚引いてそのラウンドの手札にする。', 1, 'source_bound', 'dune-uprising:rule:round.start', 'dune-uprising:binding:round.start', 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf', 'dune-uprising:rulebook:round-structure', '{}'::jsonb),
    (v_ruleset_id, 'turn.agent-or-reveal', 'turn', '自分の手番ではエージェント手番か公開手番のどちらかを行う。公開手番を行った後は、そのフェイズ中の以後の自分の手番を行わない。', 0, 'source_bound', 'dune-uprising:rule:turn.agent-or-reveal', 'dune-uprising:binding:turn.agent-or-reveal', 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf', 'dune-uprising:rulebook:player-turns', '{}'::jsonb),
    (v_ruleset_id, 'action.agent-card-link', 'action', 'エージェントをボードスペースへ送るには、そのスペースへ送れるエージェントアイコンを持つカードをプレイする必要がある。', 1, 'source_bound', 'dune-uprising:rule:action.agent-card-link', 'dune-uprising:binding:action.agent-card-link', 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf', 'dune-uprising:rulebook:overview', '{}'::jsonb),
    (v_ruleset_id, 'spy.infiltrate', 'action', '自分のスパイが接続しているボードスペースへエージェントを送るとき、そのスパイを回収すれば、相手のエージェントが既にいるスペースにも侵入できる。', 2, 'source_bound', 'dune-uprising:rule:spy.infiltrate', 'dune-uprising:binding:spy.infiltrate', 'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-3-spies/', 'dune-uprising:spies:basics', '{}'::jsonb),
    (v_ruleset_id, 'spy.gather-intelligence', 'action', '自分のスパイが接続しているボードスペースへエージェントを送るとき、スペースやカードの効果を処理する前にそのスパイを回収するとカードを1枚引ける。', 3, 'source_bound', 'dune-uprising:rule:spy.gather-intelligence', 'dune-uprising:binding:spy.gather-intelligence', 'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-3-spies/', 'dune-uprising:spies:basics', '{}'::jsonb),
    (v_ruleset_id, 'combat.sandworm', 'conflict_resolution', 'サンドワームは戦力3で、駐屯地には置かれず紛争へ直接投入される。紛争に自分のサンドワームが1体以上いる場合、獲得できる紛争報酬を倍にする。', 0, 'source_bound', 'dune-uprising:rule:combat.sandworm', 'dune-uprising:binding:combat.sandworm', 'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-2-sandworms-conflicts-and-the-shield-wall/', 'dune-uprising:sandworms:basics', '{}'::jsonb),
    (v_ruleset_id, 'combat.battle-icons', 'scoring', '紛争で1位になったプレイヤーはその紛争カードを受け取る。自分の前に同じ種類のバトルアイコンが2個そろうと、その2枚を裏返して直ちに勝利ポイント1点を得る。', 1, 'source_bound', 'dune-uprising:rule:combat.battle-icons', 'dune-uprising:binding:combat.battle-icons', 'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-2-sandworms-conflicts-and-the-shield-wall/', 'dune-uprising:battle-icons:basics', '{}'::jsonb),
    (v_ruleset_id, 'variant.choam-module-boundary', 'exception', 'CHOAM契約は任意のモジュールである。CHOAMモジュールを使わないゲームでは、契約アイコンを解決すると契約を取る代わりに2ソラリを得る。', 0, 'source_bound', 'dune-uprising:rule:variant.choam-module-boundary', 'dune-uprising:binding:variant.choam-module-boundary', 'https://news.direwolfdigital.com/dune-imperium-uprising-design-diary-4-contracts/', 'dune-uprising:choam:boundary', '{"boundary":"optional_module_not_base_authority"}'::jsonb),
    (v_ruleset_id, 'game-end.trigger', 'game_end', 'ラウンド終了時にいずれかのプレイヤーが勝利ポイント10点以上に到達している、または紛争デッキが空ならゲームを終了する。', 0, 'source_bound', 'dune-uprising:rule:game-end.trigger', 'dune-uprising:binding:game-end.trigger', 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf', 'dune-uprising:rulebook:overview', '{}'::jsonb),
    (v_ruleset_id, 'victory.most-vp', 'victory', 'ゲーム終了時に最も多くの勝利ポイントを持つプレイヤーが勝者となる。', 0, 'source_bound', 'dune-uprising:rule:victory.most-vp', 'dune-uprising:binding:victory.most-vp', 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf', 'dune-uprising:rulebook:overview', '{}'::jsonb)
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
    'dune-uprising:rule:' || rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement', rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_source_normalization","audit_date":"2026-08-22"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id IN (
      'setup.deck-and-agents','round.structure','round.start','turn.agent-or-reveal',
      'action.agent-card-link','spy.infiltrate','spy.gather-intelligence',
      'combat.sandworm','combat.battle-icons','variant.choam-module-boundary',
      'game-end.trigger','victory.most-vp'
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
    ('dune-uprising:binding:setup.deck-and-agents','dune-uprising:rule:setup.deck-and-agents','publisher:direwolf:dune-uprising:main-rulebook-2023-10-12','dune-uprising:rulebook:overview','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:round.structure','dune-uprising:rule:round.structure','publisher:direwolf:dune-uprising:main-rulebook-2023-10-12','dune-uprising:rulebook:round-structure','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:round.start','dune-uprising:rule:round.start','publisher:direwolf:dune-uprising:main-rulebook-2023-10-12','dune-uprising:rulebook:round-structure','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:turn.agent-or-reveal','dune-uprising:rule:turn.agent-or-reveal','publisher:direwolf:dune-uprising:main-rulebook-2023-10-12','dune-uprising:rulebook:player-turns','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:action.agent-card-link','dune-uprising:rule:action.agent-card-link','publisher:direwolf:dune-uprising:main-rulebook-2023-10-12','dune-uprising:rulebook:overview','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:spy.infiltrate','dune-uprising:rule:spy.infiltrate','publisher:direwolf:dune-uprising:spies-design-note','dune-uprising:spies:basics','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:spy.gather-intelligence','dune-uprising:rule:spy.gather-intelligence','publisher:direwolf:dune-uprising:spies-design-note','dune-uprising:spies:basics','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:combat.sandworm','dune-uprising:rule:combat.sandworm','publisher:direwolf:dune-uprising:sandworms-design-note','dune-uprising:sandworms:basics','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:combat.battle-icons','dune-uprising:rule:combat.battle-icons','publisher:direwolf:dune-uprising:sandworms-design-note','dune-uprising:battle-icons:basics','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:variant.choam-module-boundary','dune-uprising:rule:variant.choam-module-boundary','publisher:direwolf:dune-uprising:contracts-design-note','dune-uprising:choam:boundary','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:game-end.trigger','dune-uprising:rule:game-end.trigger','publisher:direwolf:dune-uprising:main-rulebook-2023-10-12','dune-uprising:rulebook:overview','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
    ('dune-uprising:binding:victory.most-vp','dune-uprising:rule:victory.most-vp','publisher:direwolf:dune-uprising:main-rulebook-2023-10-12','dune-uprising:rulebook:overview','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now())
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
