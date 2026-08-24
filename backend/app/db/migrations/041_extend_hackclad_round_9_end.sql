BEGIN;

-- Canonical scope: base HacKClaD physical game only.
-- The official tournament page is used only where it explicitly states the
-- normal-rule game end. Tournament time limits, team scoring, and later
-- HacKClaD editions/variants are excluded.
INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES (
  'publisher:susabi:hackclad:first-official-tournament',
  'https://www.hackclad.jp/event/%E7%AC%AC1%E5%9B%9E%E5%85%AC%E5%BC%8F%E5%A4%A7%E4%BC%9A',
  'HacKClaD official website - 第1回公式大会',
  'publisher_event_page',
  'SUSABI GAMES',
  'physical',
  'ja',
  'base-normal-end-reference',
  '{"authority":"publisher","audit_date":"2026-08-24","scope":"normal_rule_round_9_end_only","excluded":"tournament_time_limit_team_scoring_and_tiebreak"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,
  document_identity=EXCLUDED.document_identity,
  source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,
  platform=EXCLUDED.platform,
  language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,
  trust_metadata=EXCLUDED.trust_metadata,
  updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES (
  'hackclad:event:round-9-end',
  'publisher:susabi:hackclad:first-official-tournament',
  'ゲームの終了と勝者の判定',
  '9ラウンドの終わりまで進行するとゲームは終了となり、通常ルールと同様の方法でVPを計算します。'
)
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,
  section_heading=EXCLUDED.section_heading,
  external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_ruleset_id uuid;
BEGIN
  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  JOIN public.games g ON g.id=rs.game_id
  WHERE g.slug='hack-clad'
    AND rs.platform='physical'
    AND rs.language_code='ja'
    AND rs.edition_label='基本セット HacKClaD（通常版）'
    AND rs.revision_label='base-official-web-2026-08-23'
    AND rs.verification_status='source_bound'
    AND rs.is_active
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound base HacKClaD RuleSet is required';
  END IF;

  UPDATE public.rule_sets
  SET source_ids=(
        SELECT ARRAY(
          SELECT DISTINCT source_id
          FROM unnest(source_ids || ARRAY['publisher:susabi:hackclad:first-official-tournament']::text[]) AS source_id
          ORDER BY source_id
        )
      ),
      source_revision='Official website + base-rules FAQ + publisher normal-rule round-9 end reference; audited 2026-08-24',
      updated_at=now()
  WHERE id=v_ruleset_id;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES (
    v_ruleset_id,
    'game.end-round-9',
    'game_end',
    '第9ラウンドの終了時にゲームは終了する。',
    100,
    'source_bound',
    'hackclad:rule:game.end-round-9',
    'hackclad:binding:game.end-round-9',
    'https://www.hackclad.jp/event/%E7%AC%AC1%E5%9B%9E%E5%85%AC%E5%BC%8F%E5%A4%A7%E4%BC%9A',
    'hackclad:event:round-9-end',
    '{"scope":"normal_rule_end_trigger_only","excluded":"tournament_time_limit_team_scoring_and_tiebreak"}'::jsonb
  )
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,
    normalized_statement=EXCLUDED.normalized_statement,
    sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,
    source_claim_ref=EXCLUDED.source_claim_ref,
    evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,
    source_locator=EXCLUDED.source_locator,
    metadata=EXCLUDED.metadata,
    updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,
    lifecycle_status,generator_provenance
  ) VALUES (
    'hackclad:rule:game.end-round-9',
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement','第9ラウンドの終了時にゲームは終了する。'),
    'rule_node',
    'game.end-round-9',
    'accepted',
    '{"method":"publisher_event_normal_rule_reference_normalization","audit_date":"2026-08-24","scope":"base_hackclad_round_9_end_only"}'::jsonb
  )
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,
    claim_type=EXCLUDED.claim_type,
    normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,
    rule_id=EXCLUDED.rule_id,
    lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,
    updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,
    reviewer_provenance,generator_provenance,verified_at
  ) VALUES (
    'hackclad:binding:game.end-round-9',
    'hackclad:rule:game.end-round-9',
    'publisher:susabi:hackclad:first-official-tournament',
    'hackclad:event:round-9-end',
    'supports',
    '{"review":"publisher_source","scope":"normal_rule_end_trigger_only"}'::jsonb,
    '{}'::jsonb,
    now()
  )
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,
    source_id=EXCLUDED.source_id,
    locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,
    verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 12 THEN
    RAISE EXCEPTION 'HacKClaD source-bound RuleNode count must be 12';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 12 THEN
    RAISE EXCEPTION 'HacKClaD accepted Claim count must be 12';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 12 THEN
    RAISE EXCEPTION 'HacKClaD supporting EvidenceBinding count must be 12';
  END IF;
END $$;

COMMIT;
