BEGIN;

-- Normalize official rule-document roles to the canonical vocabulary used by
-- Claim / Evidence ingestion. Authority/trust remains separate in trust_metadata.
UPDATE public.evidence_sources
SET source_type = CASE source_type
    WHEN 'publisher_rulebook' THEN 'rulebook'
    WHEN 'publisher_rules_faq_page' THEN 'official_faq'
    WHEN 'publisher_errata' THEN 'official_errata'
    WHEN 'publisher_clarification' THEN 'official_clarification'
    ELSE source_type
  END,
  updated_at = now()
WHERE source_type IN (
  'publisher_rulebook',
  'publisher_rules_faq_page',
  'publisher_errata',
  'publisher_clarification'
);

-- Do not let future writes reintroduce the superseded aliases. Other source
-- roles (for example product pages or platform rules) remain valid and keep
-- their own semantics instead of being forced into an official-rule role.
ALTER TABLE public.evidence_sources
  DROP CONSTRAINT IF EXISTS evidence_sources_no_legacy_official_source_type;

ALTER TABLE public.evidence_sources
  ADD CONSTRAINT evidence_sources_no_legacy_official_source_type
  CHECK (
    source_type NOT IN (
      'publisher_rulebook',
      'publisher_rules_faq_page',
      'publisher_errata',
      'publisher_clarification'
    )
  );

COMMIT;
