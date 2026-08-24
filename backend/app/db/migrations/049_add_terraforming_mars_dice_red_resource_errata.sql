BEGIN;

-- Add a base-game icon erratum that changes resource-loss resolution.
-- Corporate Era and promo-card corrections remain outside this base RuleSet.

INSERT INTO public.source_locators (
  locator_id, source_id, page_number, section_heading, external_reference
) VALUES
  ('tm-dice:errata:red-resource-icon-discard','publisher:arclight:tm-dice:errata-2024',2,'ルール説明書 7ページ 赤枠の資源アイコン','If the targeted player has the indicated resource, make that player discard one. If they do not have it, no resource is discarded.')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,
  page_number=EXCLUDED.page_number,
  section_heading=EXCLUDED.section_heading,
  external_reference=EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT g.id INTO v_game_id
  FROM public.games g
  WHERE g.slug='terraforming-mars-the-dice-game'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE NOTICE 'Terraforming Mars: The Dice Game row not present in this fixture; skipping catalog-bound red resource icon errata extension';
    RETURN;
  END IF;

  SELECT rs.id INTO v_ruleset_id
  FROM public.rule_sets rs
  WHERE rs.game_id=v_game_id
    AND COALESCE(rs.language_code,'')='ja'
    AND COALESCE(rs.edition_label,'')='アークライト日本語版 改訂版 第2刷'
    AND COALESCE(rs.platform,'')='physical'
    AND COALESCE(rs.revision_label,'')='2024-05-30'
    AND COALESCE(rs.variant_label,'')=''
    AND rs.version=1
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Terraforming Mars Dice Japanese revised RuleSet is required';
  END IF;

  INSERT INTO public.rule_nodes(
    rule_set_id,rule_id,node_type,normalized_statement,sequence,verification_status,
    source_claim_ref,evidence_ref,source_url,source_locator,metadata
  ) VALUES
    (v_ruleset_id,'gameplay.red-resource-icon.discard','rule','赤枠の資源アイコンは、対象プレイヤーが示された資源を保有している場合、その資源1個を破棄させる。対象プレイヤーがその資源を保有していない場合、破棄は発生しない。',59,'source_bound','tm-dice:rule:gameplay.red-resource-icon.discard','tm-dice:binding:gameplay.red-resource-icon.discard','https://arclightgames.jp/wp-content/uploads/2023/12/3086b3fad2b13c82efd8eec9cd9907b9.pdf','tm-dice:errata:red-resource-icon-discard','{"errata":true,"scope":"base_game_icon"}'::jsonb)
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
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,rule_id,lifecycle_status,generator_provenance
  )
  SELECT
    'tm-dice:rule:'||rn.rule_id,
    v_ruleset_id,
    'normalized_rule_statement',
    jsonb_build_object('statement',rn.normalized_statement),
    'rule_node',
    rn.rule_id,
    'accepted',
    '{"method":"publisher_errata_normalization","audit_date":"2026-08-24","scope":"arclight_japanese_base_game"}'::jsonb
  FROM public.rule_nodes rn
  WHERE rn.rule_set_id=v_ruleset_id
    AND rn.rule_id='gameplay.red-resource-icon.discard'
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
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
    ('tm-dice:binding:gameplay.red-resource-icon.discard','tm-dice:rule:gameplay.red-resource-icon.discard','publisher:arclight:tm-dice:errata-2024','tm-dice:errata:red-resource-icon-discard','supports','{"reviewed":"2026-08-24"}'::jsonb,'{"method":"manual_primary_source_review"}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,
    source_id=EXCLUDED.source_id,
    locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,
    reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,
    verified_at=EXCLUDED.verified_at;

  IF (SELECT count(*) FROM public.rule_nodes WHERE rule_set_id=v_ruleset_id AND verification_status='source_bound') < 17 THEN
    RAISE EXCEPTION 'Terraforming Mars Dice requires at least 17 source-bound player-facing RuleNodes after red resource icon errata extension';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.rule_nodes rn
    WHERE rn.rule_set_id=v_ruleset_id AND rn.verification_status='source_bound'
      AND NOT EXISTS (
        SELECT 1 FROM public.claims c
        JOIN public.evidence_bindings eb ON eb.claim_id=c.claim_id AND eb.relation='supports'
        WHERE c.rule_set_id=v_ruleset_id AND c.rule_id=rn.rule_id AND c.lifecycle_status='accepted'
      )
  ) THEN
    RAISE EXCEPTION 'Every Terraforming Mars Dice source-bound RuleNode requires accepted supporting evidence';
  END IF;
END $$;

COMMIT;
