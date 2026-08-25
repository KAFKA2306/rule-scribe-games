BEGIN;

-- Keep one claim per independently supported rule: Chief is defined by the rulebook,
-- while the current publisher FAQ supplies the tied-maximum clarification for Fox.
DO $$
DECLARE v_game_id uuid; v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id FROM public.games WHERE slug='coyote' LIMIT 1;
  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Coyote canonical game row not present in this fixture; skipping evidence split';
    RETURN;
  END IF;

  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND COALESCE(language_code,'')='ja'
    AND COALESCE(edition_label,'')='コヨーテ（ニューゲームズオーダー日本語版）'
    AND COALESCE(platform,'')='physical'
    AND COALESCE(revision_label,'')='ngo-ja-rulebook-2026-02-20'
    AND COALESCE(variant_label,'')='' AND version=1 LIMIT 1;
  IF v_ruleset_id IS NULL THEN RAISE EXCEPTION 'Coyote source-bound RuleSet is required'; END IF;

  DELETE FROM public.evidence_bindings WHERE binding_id='coyote:binding:special.chief-fox';
  DELETE FROM public.claims WHERE claim_id='coyote:rule:special.chief-fox';
  DELETE FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND rule_id='special.chief-fox';

  INSERT INTO public.rule_nodes(rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,source_claim_ref,evidence_ref,source_url,source_locator,metadata) VALUES
  (v_ruleset_id,'special.chief','effect','酋長カードはすべての基本カードの数値を2倍にする。',100,'source_bound','coyote:rule:special.chief','coyote:binding:special.chief','https://drive.google.com/file/d/1e_hDDhv3XcnOraZ1tvl4CwpiYiq4a1bT/view','coyote:rules:chief-fox','{}'::jsonb),
  (v_ruleset_id,'special.fox','effect','キツネカードはその回に出た最大のコヨーテカード1枚の数値を0にする。最大値が複数枚あっても0になるのは1枚だけ。',105,'source_bound','coyote:rule:special.fox','coyote:binding:special.fox','https://www.newgamesorder.jp/games/coyote','coyote:product:fox-faq','{}'::jsonb)
  ON CONFLICT(rule_set_id,rule_id) DO UPDATE SET node_type=EXCLUDED.node_type,normalized_statement=EXCLUDED.normalized_statement,sequence=EXCLUDED.sequence,verification_status=EXCLUDED.verification_status,source_claim_ref=EXCLUDED.source_claim_ref,evidence_ref=EXCLUDED.evidence_ref,source_url=EXCLUDED.source_url,source_locator=EXCLUDED.source_locator,metadata=EXCLUDED.metadata,updated_at=now();

  INSERT INTO public.claims(claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance)
  SELECT 'coyote:rule:'||rule_id,v_ruleset_id,'normalized_rule_statement',jsonb_build_object('statement',normalized_statement),'rule_node',rule_id,'accepted','{"method":"publisher_primary_source_normalization","audit_date":"2026-08-25","scope":"coyote_ngo_japanese_base"}'::jsonb
  FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND rule_id IN ('special.chief','special.fox')
  ON CONFLICT(claim_id) DO UPDATE SET rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,target_type=EXCLUDED.target_type,rule_id=EXCLUDED.rule_id,lifecycle_status=EXCLUDED.lifecycle_status,generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at) VALUES
  ('coyote:binding:special.chief','coyote:rule:special.chief','publisher:ngo:coyote:rulebook-ja','coyote:rules:chief-fox','supports','{"review":"publisher_rulebook"}'::jsonb,'{}'::jsonb,now()),
  ('coyote:binding:special.fox','coyote:rule:special.fox','publisher:ngo:coyote:product-ja','coyote:product:fox-faq','supports','{"review":"publisher_faq"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') <> 13 THEN RAISE EXCEPTION 'Coyote source-bound RuleNode count must be 13 after evidence split'; END IF;
  IF (SELECT count(*) FROM public.claims WHERE rule_set_id=v_ruleset_id AND target_type='rule_node' AND lifecycle_status='accepted') <> 13 THEN RAISE EXCEPTION 'Coyote accepted Claim count must be 13 after evidence split'; END IF;
  IF (SELECT count(*) FROM public.evidence_bindings eb JOIN public.claims c ON c.claim_id=eb.claim_id WHERE c.rule_set_id=v_ruleset_id AND eb.relation='supports') <> 13 THEN RAISE EXCEPTION 'Coyote supporting EvidenceBinding count must be 13 after evidence split'; END IF;
END $$;

COMMIT;
