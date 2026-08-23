BEGIN;

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('elfenland:rules:collect','publisher:amigo:elfenland:rules-en-v3','Collecting Town Pieces','collect own Town Piece from each reached town; reduce hand to four at end of turn')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE v_ruleset_id uuid;
BEGIN
  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  JOIN public.games g ON g.id=rs.game_id
  WHERE g.slug='elfenland'
    AND rs.is_active
    AND rs.verification_status='source_bound'
    AND rs.revision_label='amigo-v3.0-2013-ja'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Elfenland AMIGO Version 3.0 RuleSet is required';
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
  (v_ruleset_id,'move.collect-town-piece','action','長靴コマが街に到着するたび、その街にある自分の訪問地コマを取り、自分の前に置く。手番を終える街でも同様に訪問地コマを回収する。',75,'source_bound','elfenland:rule:move.collect-town-piece','elfenland:binding:move.collect-town-piece','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:collect','{}'::jsonb),
  (v_ruleset_id,'turn.hand-limit','condition','移動手番の終了時に移動カードを5枚以上持っている場合、4枚になるまで余分なカードを移動カードの山へ戻す。',77,'source_bound','elfenland:rule:turn.hand-limit','elfenland:binding:turn.hand-limit','https://blog.amigo-spiele.de/content/ap/rule/02610-GB-AmigoRule.pdf','elfenland:rules:collect','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET
    node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,
    verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,
    source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT
    'elfenland:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),
    'rule_node',rule_id,'accepted','{"method":"publisher_rulebook_normalization","audit_date":"2026-08-24","scope":"elfenland_base_game_v3"}'::jsonb
  FROM public.rule_nodes
  WHERE rule_set_id=v_ruleset_id AND rule_id IN('move.collect-town-piece','turn.hand-limit')
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
  ('elfenland:binding:move.collect-town-piece','elfenland:rule:move.collect-town-piece','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:collect','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('elfenland:binding:turn.hand-limit','elfenland:rule:turn.hand-limit','publisher:amigo:elfenland:rules-en-v3','elfenland:rules:collect','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 13 THEN
    RAISE EXCEPTION 'Elfenland source-bound RuleNode count must be 13 after movement extension';
  END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 13 THEN
    RAISE EXCEPTION 'Elfenland accepted Claim count must be 13 after movement extension';
  END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 13 THEN
    RAISE EXCEPTION 'Elfenland supporting EvidenceBinding count must be 13 after movement extension';
  END IF;
END $$;

COMMIT;
