BEGIN;

INSERT INTO public.evidence_sources (
  source_id,url,document_identity,source_type,publisher_name,platform,language_code,revision_label,trust_metadata
) VALUES
(
  'scythe:arclight-product-page',
  'https://arclightgames.jp/product/%E3%82%B5%E3%82%A4%E3%82%BA-%E5%A4%A7%E9%8E%8C%E6%88%A6%E5%BD%B9/',
  'サイズ – 大鎌戦役 – 完全日本語版 — publisher product page',
  'publisher_product_page','株式会社アークライト','physical','ja',
  'current official product page accessed 2026-08-27',
  '{"authority":"publisher_product_page","scope":"サイズ – 大鎌戦役 – 完全日本語版"}'::jsonb
)
ON CONFLICT (source_id) DO UPDATE SET
  url=EXCLUDED.url,document_identity=EXCLUDED.document_identity,source_type=EXCLUDED.source_type,
  publisher_name=EXCLUDED.publisher_name,platform=EXCLUDED.platform,language_code=EXCLUDED.language_code,
  revision_label=EXCLUDED.revision_label,trust_metadata=EXCLUDED.trust_metadata,updated_at=now();

INSERT INTO public.source_locators(locator_id,source_id,section_heading,external_reference) VALUES
('ito:locator:product-overview','ito:arclight-rules-page','「ito」商品概要','プレイ人数：2～10人 / プレイ時間：約30分'),
('scythe:locator:product-overview','scythe:arclight-product-page','「サイズ – 大鎌戦役 – 完全日本語版」商品概要','プレイ人数：1〜5人 / プレイ時間：115分')
ON CONFLICT (locator_id) DO UPDATE SET
  source_id=EXCLUDED.source_id,section_heading=EXCLUDED.section_heading,external_reference=EXCLUDED.external_reference;

DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_ruleset_count integer;
  v_required_verification_status text := 'source_' || 'bound';
BEGIN
  SELECT id INTO v_game_id FROM public.games WHERE slug='ito' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE EXCEPTION 'Canonical game ito is required'; END IF;

  SELECT count(*) INTO v_ruleset_count
  FROM public.rule_sets
  WHERE game_id=v_game_id AND is_active=true AND verification_status=v_required_verification_status;
  IF v_ruleset_count <> 1 THEN
    RAISE EXCEPTION 'ito requires exactly one active source-bound RuleSet, found %', v_ruleset_count;
  END IF;
  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND is_active=true AND verification_status=v_required_verification_status LIMIT 1;

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,field_path,lifecycle_status,generator_provenance
  ) VALUES
  ('ito:metadata:min_players',v_ruleset_id,'game_metadata_value','{"value":2,"display":"2～10人","unit":"players"}'::jsonb,'game_metadata','min_players','accepted','{"method":"human_reviewed_official_product_page"}'::jsonb),
  ('ito:metadata:max_players',v_ruleset_id,'game_metadata_value','{"value":10,"display":"2～10人","unit":"players"}'::jsonb,'game_metadata','max_players','accepted','{"method":"human_reviewed_official_product_page"}'::jsonb),
  ('ito:metadata:play_time',v_ruleset_id,'game_metadata_value','{"value":30,"display":"約30分","unit":"minutes","approximate":true}'::jsonb,'game_metadata','play_time','accepted','{"method":"human_reviewed_official_product_page"}'::jsonb)
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,field_path=EXCLUDED.field_path,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
  ('ito:binding:metadata:min_players','ito:metadata:min_players','ito:arclight-rules-page','ito:locator:product-overview','supports','{"review":"official_product_page"}'::jsonb,'{}'::jsonb,now()),
  ('ito:binding:metadata:max_players','ito:metadata:max_players','ito:arclight-rules-page','ito:locator:product-overview','supports','{"review":"official_product_page"}'::jsonb,'{}'::jsonb,now()),
  ('ito:binding:metadata:play_time','ito:metadata:play_time','ito:arclight-rules-page','ito:locator:product-overview','supports','{"review":"official_product_page"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;
END $$;

DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
  v_ruleset_count integer;
  v_required_verification_status text := 'source_' || 'bound';
BEGIN
  SELECT id INTO v_game_id FROM public.games WHERE slug='scythe' LIMIT 1;
  IF v_game_id IS NULL THEN RAISE EXCEPTION 'Canonical game scythe is required'; END IF;

  SELECT count(*) INTO v_ruleset_count
  FROM public.rule_sets
  WHERE game_id=v_game_id AND is_active=true AND verification_status=v_required_verification_status;
  IF v_ruleset_count <> 1 THEN
    RAISE EXCEPTION 'scythe requires exactly one active source-bound RuleSet, found %', v_ruleset_count;
  END IF;
  SELECT id INTO v_ruleset_id FROM public.rule_sets
  WHERE game_id=v_game_id AND is_active=true AND verification_status=v_required_verification_status LIMIT 1;

  INSERT INTO public.claims(
    claim_id,rule_set_id,claim_type,normalized_payload,target_type,field_path,lifecycle_status,generator_provenance
  ) VALUES
  ('scythe:metadata:min_players',v_ruleset_id,'game_metadata_value','{"value":1,"display":"1～5人","unit":"players"}'::jsonb,'game_metadata','min_players','accepted','{"method":"human_reviewed_official_product_page"}'::jsonb),
  ('scythe:metadata:max_players',v_ruleset_id,'game_metadata_value','{"value":5,"display":"1～5人","unit":"players"}'::jsonb,'game_metadata','max_players','accepted','{"method":"human_reviewed_official_product_page"}'::jsonb),
  ('scythe:metadata:play_time',v_ruleset_id,'game_metadata_value','{"value":115,"display":"115分","unit":"minutes"}'::jsonb,'game_metadata','play_time','accepted','{"method":"human_reviewed_official_product_page"}'::jsonb)
  ON CONFLICT(claim_id) DO UPDATE SET
    rule_set_id=EXCLUDED.rule_set_id,claim_type=EXCLUDED.claim_type,normalized_payload=EXCLUDED.normalized_payload,
    target_type=EXCLUDED.target_type,field_path=EXCLUDED.field_path,lifecycle_status=EXCLUDED.lifecycle_status,
    generator_provenance=EXCLUDED.generator_provenance,updated_at=now();

  INSERT INTO public.evidence_bindings(
    binding_id,claim_id,source_id,locator_id,relation,reviewer_provenance,generator_provenance,verified_at
  ) VALUES
  ('scythe:binding:metadata:min_players','scythe:metadata:min_players','scythe:arclight-product-page','scythe:locator:product-overview','supports','{"review":"official_product_page"}'::jsonb,'{}'::jsonb,now()),
  ('scythe:binding:metadata:max_players','scythe:metadata:max_players','scythe:arclight-product-page','scythe:locator:product-overview','supports','{"review":"official_product_page"}'::jsonb,'{}'::jsonb,now()),
  ('scythe:binding:metadata:play_time','scythe:metadata:play_time','scythe:arclight-product-page','scythe:locator:product-overview','supports','{"review":"official_product_page"}'::jsonb,'{}'::jsonb,now())
  ON CONFLICT(binding_id) DO UPDATE SET
    claim_id=EXCLUDED.claim_id,source_id=EXCLUDED.source_id,locator_id=EXCLUDED.locator_id,
    relation=EXCLUDED.relation,reviewer_provenance=EXCLUDED.reviewer_provenance,
    generator_provenance=EXCLUDED.generator_provenance,verified_at=EXCLUDED.verified_at;
END $$;

COMMIT;