BEGIN;

-- 現行Skull King RuleSetの0ビッド得点を、既存の正準Concept「ビッド」へ結ぶ。
-- RuleNode、Claim、Evidenceがすべて確認済みの場合だけ追加する。
-- RuleNodeの出典状態はmetadataで保持し、このConcept関連自体は明示確認済みとしてverifiedにする。

DO $$
DECLARE
  v_ruleset_id uuid;
BEGIN
  SELECT rs.id
    INTO v_ruleset_id
  FROM public.rule_sets rs
  JOIN public.games g ON g.id = rs.game_id
  WHERE g.slug = 'skull-king'
    AND rs.is_active = true
    AND rs.status = 'active'
    AND COALESCE(rs.language_code, '') = 'en'
    AND COALESCE(rs.edition_label, '') = 'Grandpa Beck''s Games current edition'
    AND COALESCE(rs.platform, '') = 'physical'
    AND COALESCE(rs.revision_label, '') = 'current-web-rulebook-1764178570'
    AND COALESCE(rs.variant_label, '') = ''
    AND rs.version = 1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active current Skull King RuleSet is required before linking zero-bid concept';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.claims c
      ON c.claim_id = rn.source_claim_ref
     AND c.rule_set_id = rn.rule_set_id
     AND c.lifecycle_status = 'accepted'
    JOIN public.evidence_bindings eb
      ON eb.binding_id = rn.evidence_ref
     AND eb.claim_id = c.claim_id
     AND eb.relation = 'supports'
    WHERE rn.rule_set_id = v_ruleset_id
      AND rn.rule_id = 'scoring.zero-bid'
      AND rn.source_claim_ref = 'skull-king:current:rule:scoring.zero-bid'
      AND rn.evidence_ref = 'skull-king:current:binding:scoring.zero-bid'
      AND rn.source_locator = 'skull-king:rulebook:scoring'
      AND rn.verification_status IN ('source_bound', 'verified')
      AND eb.source_id = 'publisher:grandpa-becks:skull-king:current-rulebook'
  ) THEN
    RAISE EXCEPTION 'Current Skull King zero-bid claim/evidence binding is required';
  END IF;

  INSERT INTO public.rule_node_concepts (
    rule_set_id,
    rule_id,
    concept_id,
    reference_kind,
    verification_status,
    source_url,
    source_locator,
    metadata
  )
  SELECT
    rn.rule_set_id,
    rn.rule_id,
    'player-action.bid',
    'mentions',
    'verified',
    rn.source_url,
    rn.source_locator,
    jsonb_build_object(
      'source_claim_ref', rn.source_claim_ref,
      'evidence_ref', rn.evidence_ref,
      'source_rule_verification_status', rn.verification_status,
      'scope', COALESCE(rn.metadata->>'scope', 'base'),
      'condition', COALESCE(rn.metadata->'condition', 'null'::jsonb),
      'migration', '123_link_skull_king_zero_bid_concept'
    )
  FROM public.rule_nodes rn
  JOIN public.concepts c ON c.concept_id = 'player-action.bid'
  JOIN public.claims claim
    ON claim.claim_id = rn.source_claim_ref
   AND claim.rule_set_id = rn.rule_set_id
   AND claim.lifecycle_status = 'accepted'
  JOIN public.evidence_bindings binding
    ON binding.binding_id = rn.evidence_ref
   AND binding.claim_id = claim.claim_id
   AND binding.relation = 'supports'
  WHERE rn.rule_set_id = v_ruleset_id
    AND rn.rule_id = 'scoring.zero-bid'
    AND rn.verification_status IN ('source_bound', 'verified')
    AND rn.source_claim_ref IS NOT NULL
    AND rn.evidence_ref IS NOT NULL
  ON CONFLICT (rule_set_id, rule_id, concept_id, reference_kind) DO UPDATE SET
    verification_status = EXCLUDED.verification_status,
    source_url = EXCLUDED.source_url,
    source_locator = EXCLUDED.source_locator,
    metadata = EXCLUDED.metadata;

  IF (
    SELECT count(*)
    FROM public.rule_node_concepts rnc
    WHERE rnc.rule_set_id = v_ruleset_id
      AND rnc.rule_id = 'scoring.zero-bid'
      AND rnc.concept_id = 'player-action.bid'
      AND rnc.reference_kind = 'mentions'
      AND rnc.verification_status = 'verified'
      AND rnc.source_locator = 'skull-king:rulebook:scoring'
      AND rnc.metadata->>'source_rule_verification_status' IN ('source_bound', 'verified')
  ) <> 1 THEN
    RAISE EXCEPTION 'Expected one verified zero-bid concept reference on the active RuleSet';
  END IF;
END $$;

COMMIT;
