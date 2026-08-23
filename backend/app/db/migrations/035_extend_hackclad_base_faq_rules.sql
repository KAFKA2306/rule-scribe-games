BEGIN;

-- Extend only the existing base HacKClaD physical/ja RuleSet with additional
-- first-party rulings from the publisher's basic-rules FAQ section.
-- CROSS FATE and later expansion/variant sections remain out of scope.
INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('hackclad:faq:effect-movement','publisher:susabi:hackclad:faq','①基本ルールに関するFAQ','スキルやノックバックでクラッドが移動した場合も移動攻撃として扱いますか？'),
('hackclad:faq:knockback-order','publisher:susabi:hackclad:faq','①基本ルールに関するFAQ','ノックバックを含むスキルカードの処理順はどうなりますか？'),
('hackclad:faq:multiple-missions','publisher:susabi:hackclad:faq','①基本ルールに関するFAQ','複数のミッションを同時に達成できますか？'),
('hackclad:faq:card-use-established','publisher:susabi:hackclad:faq','①基本ルールに関するFAQ','カードを使用したことになるタイミングはいつですか？')
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

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'reaction.effect-caused-movement','exception','スキルカードの効果やノックバックによってクラッドが移動した場合も移動攻撃として扱い、移動先にいるウィッチは対応アクションを実行できる。',0,'source_bound','hackclad:rule:reaction.effect-caused-movement','hackclad:binding:reaction.effect-caused-movement','https://www.hackclad.jp/FAQ','hackclad:faq:effect-movement','{}'::jsonb),
  (v_ruleset_id,'action.knockback-resolution-order','action','ノックバックを含むスキルカードは、ノックバック以外の処理を行い、そのスキルカードを捨て札にした後でクラッドをノックバックによって移動させる。',0,'source_bound','hackclad:rule:action.knockback-resolution-order','hackclad:binding:action.knockback-resolution-order','https://www.hackclad.jp/FAQ','hackclad:faq:knockback-order','{}'::jsonb),
  (v_ruleset_id,'condition.multiple-missions','condition','条件を満たしている場合、複数のミッションを同時に達成できる。',0,'source_bound','hackclad:rule:condition.multiple-missions','hackclad:binding:condition.multiple-missions','https://www.hackclad.jp/FAQ','hackclad:faq:multiple-missions','{}'::jsonb),
  (v_ruleset_id,'action.card-use-established','condition','スキルカードは、必要なコストを支払い、使用条件を満たした時点で使用したものとして扱う。',0,'source_bound','hackclad:rule:action.card-use-established','hackclad:binding:action.card-use-established','https://www.hackclad.jp/FAQ','hackclad:faq:card-use-established','{}'::jsonb)
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
  )
  SELECT
    'hackclad:rule:'||rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement',normalized_statement),
    'rule_node',
    rule_id,
    'accepted',
    '{"method":"publisher_faq_normalization","audit_date":"2026-08-24","scope":"base_hackclad_basic_faq_only"}'::jsonb
  FROM public.rule_nodes
  WHERE rule_set_id=v_ruleset_id
    AND rule_id IN(
      'reaction.effect-caused-movement',
      'action.knockback-resolution-order',
      'condition.multiple-missions',
      'action.card-use-established'
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
  ) VALUES
  ('hackclad:binding:reaction.effect-caused-movement','hackclad:rule:reaction.effect-caused-movement','publisher:susabi:hackclad:faq','hackclad:faq:effect-movement','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
  ('hackclad:binding:action.knockback-resolution-order','hackclad:rule:action.knockback-resolution-order','publisher:susabi:hackclad:faq','hackclad:faq:knockback-order','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
  ('hackclad:binding:condition.multiple-missions','hackclad:rule:condition.multiple-missions','publisher:susabi:hackclad:faq','hackclad:faq:multiple-missions','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now()),
  ('hackclad:binding:action.card-use-established','hackclad:rule:action.card-use-established','publisher:susabi:hackclad:faq','hackclad:faq:card-use-established','supports','{"review":"publisher_source"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,
    source_id=EXCLUDED.source_id,
    locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,
    verified_at=EXCLUDED.verified_at;
END $$;

COMMIT;
