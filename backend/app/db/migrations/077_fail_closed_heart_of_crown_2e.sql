BEGIN;

-- Player-facing success condition:
-- The canonical physical Heart of Crown 2nd Edition page must not publish
-- legacy rule text or edition-sensitive metadata as settled facts until those
-- claims are bound to an exact first-party physical Second Edition source.
--
-- Identity authority is the current FLIPFLOPs product surface. The older
-- 2012 first-edition manual and HEART of CROWN Online are intentionally not
-- promoted to physical Second Edition rule authority.

INSERT INTO public.evidence_sources (
  source_id,
  url,
  document_identity,
  source_type,
  publisher_name,
  platform,
  language_code,
  revision_label,
  trust_metadata
) VALUES (
  'publisher:flipflops:heart-of-crown-2e:product',
  'https://games.flipflops.jp/heartofcrown',
  'ハートオブクラウン 第二版 — FLIPFLOPs official product surface',
  'publisher_product_page',
  'FLIPFLOPs',
  'physical',
  'ja',
  'current-second-edition-product',
  '{"authority":"official_publisher_identity_surface","audit_date":"2026-08-28","scope":"physical_second_edition_identity_only","rule_authority":false}'::jsonb
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

UPDATE public.games
SET
  title = 'Heart of Crown 2nd Edition',
  title_ja = 'ハートオブクラウン 第二版',
  title_en = 'Heart of Crown 2nd Edition',
  description = 'FLIPFLOPsによるデッキ構築型カードゲーム「ハートオブクラウン」の第二版。',
  summary = '物理版第二版のルール詳細は、版を特定できる一次ルール資料への結び付けを確認中です。',
  identity_status = 'verified',
  identity_source = 'https://games.flipflops.jp/heartofcrown',
  source_url = 'https://games.flipflops.jp/heartofcrown',
  source_trust = 'official_publisher',
  content_review_status = 'review_required',
  is_official = true,
  edition_label = '第二版 基本セット',
  language_code = 'ja',
  publisher = 'FLIPFLOPs',
  source_revision = 'physical Second Edition identity verified; exact physical rulebook not source-bound; audited 2026-08-28',
  rules = '{}'::jsonb,
  rules_content = NULL,
  structured_data = '{}'::jsonb,
  setup_summary = NULL,
  gameplay_summary = NULL,
  end_game_summary = NULL,
  play_time = NULL,
  play_time_min_minutes = NULL,
  play_time_max_minutes = NULL,
  min_age = NULL,
  published_year = NULL,
  updated_at = now()
WHERE slug = 'heart-of-crown-2nd-edition';

-- The generic duplicate remains retired. Do not copy its historical rule text,
-- edition-sensitive metadata, or cumulative view counter into the canonical row.

COMMIT;
