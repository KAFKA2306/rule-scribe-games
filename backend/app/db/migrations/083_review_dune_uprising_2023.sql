BEGIN;

-- Player-facing success condition:
-- Dune: Imperium – Uprising may return to search only when the exact standalone
-- physical 2023 RuleSet has 12 source-bound RuleNodes, 12 accepted rule claims,
-- and 12 supporting evidence bindings, all backed by first-party Dire Wolf
-- Uprising sources. The original Dune: Imperium, its expansions, Uprising
-- six-player supplement, and the 2026 digital implementation remain separate.
DO $$
DECLARE
  v_game_id uuid;
  v_ruleset_id uuid;
BEGIN
  SELECT id INTO v_game_id
  FROM public.games
  WHERE slug = 'dune-imperium-uprising'
  LIMIT 1;

  IF v_game_id IS NULL THEN
    RAISE EXCEPTION 'Canonical Dune: Imperium - Uprising game row is required';
  END IF;

  SELECT id INTO v_ruleset_id
  FROM public.rule_sets
  WHERE game_id = v_game_id
    AND is_active = true
    AND status = 'active'
    AND verification_status = ('source' || '_' || 'bound')
    AND COALESCE(edition_label, '') = 'Dune: Imperium – Uprising standalone physical (2023)'
    AND COALESCE(language_code, '') = 'ja'
    AND COALESCE(platform, '') = 'physical'
    AND COALESCE(revision_label, '') = '2023-10-12'
  LIMIT 1;

  IF v_ruleset_id IS NULL THEN
    RAISE EXCEPTION 'Active source-bound Dune: Imperium - Uprising 2023 physical RuleSet is required';
  END IF;

  IF (
    SELECT count(*)
    FROM public.rule_nodes
    WHERE rule_set_id = v_ruleset_id
      AND verification_status = ('source' || '_' || 'bound')
  ) <> 12 THEN
    RAISE EXCEPTION 'Dune: Imperium - Uprising requires exactly 12 source-bound RuleNodes';
  END IF;

  IF (
    SELECT count(*)
    FROM public.claims
    WHERE rule_set_id = v_ruleset_id
      AND target_type = 'rule_node'
      AND lifecycle_status = 'accepted'
  ) <> 12 THEN
    RAISE EXCEPTION 'Dune: Imperium - Uprising requires exactly 12 accepted rule claims';
  END IF;

  IF (
    SELECT count(*)
    FROM public.evidence_bindings eb
    JOIN public.claims c ON c.claim_id = eb.claim_id
    WHERE c.rule_set_id = v_ruleset_id
      AND c.target_type = 'rule_node'
      AND c.lifecycle_status = 'accepted'
      AND eb.relation = 'supports'
  ) <> 12 THEN
    RAISE EXCEPTION 'Dune: Imperium - Uprising requires exactly 12 supporting evidence bindings';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    LEFT JOIN public.claims c
      ON c.claim_id = rn.source_claim_ref
      AND c.rule_set_id = rn.rule_set_id
      AND c.lifecycle_status = 'accepted'
    LEFT JOIN public.evidence_bindings eb
      ON eb.binding_id = rn.evidence_ref
      AND eb.claim_id = c.claim_id
      AND eb.relation = 'supports'
    WHERE rn.rule_set_id = v_ruleset_id
      AND (c.claim_id IS NULL OR eb.binding_id IS NULL)
  ) THEN
    RAISE EXCEPTION 'Every Dune: Imperium - Uprising RuleNode must resolve to accepted supporting evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    WHERE rn.rule_set_id = v_ruleset_id
      AND eb.source_id NOT IN (
        'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12',
        'publisher:direwolf:dune-uprising:spies-design-note',
        'publisher:direwolf:dune-uprising:sandworms-design-note',
        'publisher:direwolf:dune-uprising:contracts-design-note'
      )
  ) THEN
    RAISE EXCEPTION 'Dune: Imperium - Uprising rules must use only approved first-party 2023 Uprising rule sources';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    JOIN public.evidence_bindings eb ON eb.binding_id = rn.evidence_ref
    JOIN public.evidence_sources es ON es.source_id = eb.source_id
    WHERE rn.rule_set_id = v_ruleset_id
      AND es.publisher_name <> 'Dire Wolf Digital'
  ) THEN
    RAISE EXCEPTION 'Dune: Imperium - Uprising rule evidence must remain first-party Dire Wolf evidence';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12'
      AND url = 'https://www.direwolfdigital.com/assets/dune/DUNE_IMPERIUM_UPRISING_Main_Rulebook_23-10-12.pdf'
      AND revision_label = '2023-10-12'
      AND publisher_name = 'Dire Wolf Digital'
      AND source_type = 'publisher_rulebook'
  ) THEN
    RAISE EXCEPTION 'Dire Wolf 2023-10-12 Uprising main rulebook is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:direwolf:dune-uprising:product'
      AND publisher_name = 'Dire Wolf Digital'
      AND source_type = 'publisher_product_page'
  ) THEN
    RAISE EXCEPTION 'Dire Wolf Uprising product identity source is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.evidence_sources
    WHERE source_id = 'publisher:direwolf:dune-uprising:resources'
      AND url = 'https://www.direwolfdigital.com/dune-imperium/resources/'
      AND publisher_name = 'Dire Wolf Digital'
      AND source_type = 'publisher_resources_page'
  ) THEN
    RAISE EXCEPTION 'Dire Wolf Uprising resources source is required';
  END IF;

  IF NOT (
    SELECT ARRAY[
      'publisher:direwolf:dune-uprising:product',
      'publisher:direwolf:dune-uprising:resources',
      'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12',
      'publisher:direwolf:dune-uprising:spies-design-note',
      'publisher:direwolf:dune-uprising:sandworms-design-note',
      'publisher:direwolf:dune-uprising:contracts-design-note'
    ]::text[] <@ source_ids
    FROM public.rule_sets
    WHERE id = v_ruleset_id
  ) THEN
    RAISE EXCEPTION 'Dune: Imperium - Uprising RuleSet must preserve product, resources, rulebook, and design-note source distinctions';
  END IF;

  UPDATE public.games
  SET content_review_status = 'human_reviewed',
      published_year = 2023,
      source_revision = 'Dire Wolf standalone physical Uprising 2023 identity + 2023-10-12 main rulebook and first-party Uprising design notes; original Dune: Imperium, expansions, six-player supplement, and 2026 digital implementation excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_game_id;

  UPDATE public.rule_sets
  SET source_revision = 'Dire Wolf standalone physical Uprising 2023 identity + 2023-10-12 main rulebook and first-party Uprising design notes; original Dune: Imperium, expansions, six-player supplement, and 2026 digital implementation excluded; human-reviewed 2026-08-28',
      updated_at = now()
  WHERE id = v_ruleset_id;

  UPDATE public.evidence_sources
  SET trust_metadata = COALESCE(trust_metadata, '{}'::jsonb)
      || '{"review_date":"2026-08-28","review_status":"human_reviewed","scope":"dune_imperium_uprising_standalone_physical_2023"}'::jsonb,
      updated_at = now()
  WHERE source_id IN (
    'publisher:direwolf:dune-uprising:product',
    'publisher:direwolf:dune-uprising:resources',
    'publisher:direwolf:dune-uprising:main-rulebook-2023-10-12',
    'publisher:direwolf:dune-uprising:spies-design-note',
    'publisher:direwolf:dune-uprising:sandworms-design-note',
    'publisher:direwolf:dune-uprising:contracts-design-note'
  );
END $$;

COMMIT;
