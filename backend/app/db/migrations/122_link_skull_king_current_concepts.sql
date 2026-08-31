BEGIN;

-- 現行Skull King RuleSetへ、既存の正準Conceptを結び直す。
-- 016のリンクは旧RuleSetの履歴として保持し、active RuleSetだけに新しい参照を追加する。
-- 公式一次資料で現在のRuleNodeと対応を確認できるものだけを対象にし、
-- 対応するRuleNodeがないTrump Suitは推測で結ばない。

DO $$
DECLARE
  v_ruleset_id uuid;
  v_inserted integer;
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
    RAISE EXCEPTION 'Active current Skull King RuleSet is required before linking concepts';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    WHERE rn.rule_set_id = v_ruleset_id
      AND rn.rule_id = 'resolution.mermaid-triad'
      AND rn.source_claim_ref = 'skull-king:current:rule:resolution.mermaid-triad'
      AND rn.evidence_ref = 'skull-king:current:binding:resolution.mermaid-triad'
      AND rn.source_locator = 'skull-king:faq:mermaid-triad'
      AND rn.verification_status IN ('source_bound', 'verified')
  ) THEN
    RAISE EXCEPTION 'Current Skull King Mermaid FAQ claim/evidence binding is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM public.rule_nodes rn
    WHERE rn.rule_set_id = v_ruleset_id
      AND rn.rule_id = 'two-player.tigress'
      AND rn.source_claim_ref = 'skull-king:current:rule:two-player.tigress'
      AND rn.evidence_ref = 'skull-king:current:binding:two-player.tigress'
      AND rn.source_locator = 'skull-king:faq:graybeard-tigress'
      AND rn.metadata->>'scope' = 'two_player'
      AND rn.metadata->'condition'->>'player_count' = '2'
      AND rn.verification_status IN ('source_bound', 'verified')
  ) THEN
    RAISE EXCEPTION 'Current Skull King two-player Tigress FAQ claim/evidence binding is required';
  END IF;

  WITH links(rule_id, concept_id, reference_kind) AS (
    VALUES
      ('round.bid', 'player-action.bid', 'defines'),
      ('scoring.bid-one-plus', 'player-action.bid', 'mentions'),
      ('resolution.mermaid-triad', 'rule-pattern.trick', 'mentions'),
      ('turn.follow-suit', 'component.special-card', 'mentions'),
      ('resolution.mermaid-triad', 'component.special-card', 'mentions'),
      ('two-player.tigress', 'component.special-card', 'modifies')
  ), source_rows AS (
    SELECT
      rn.rule_set_id,
      rn.rule_id,
      links.concept_id,
      links.reference_kind,
      rn.verification_status,
      rn.source_url,
      rn.source_locator,
      jsonb_build_object(
        'source_claim_ref', rn.source_claim_ref,
        'evidence_ref', rn.evidence_ref,
        'scope', COALESCE(rn.metadata->>'scope', 'base'),
        'condition', COALESCE(rn.metadata->'condition', 'null'::jsonb),
        'migration', '122_link_skull_king_current_concepts'
      ) AS metadata
    FROM links
    JOIN public.rule_nodes rn
      ON rn.rule_set_id = v_ruleset_id
     AND rn.rule_id = links.rule_id
    JOIN public.concepts c
      ON c.concept_id = links.concept_id
    WHERE rn.verification_status IN ('source_bound', 'verified')
      AND rn.source_claim_ref IS NOT NULL
      AND rn.evidence_ref IS NOT NULL
  )
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
    rule_set_id,
    rule_id,
    concept_id,
    reference_kind,
    verification_status,
    source_url,
    source_locator,
    metadata
  FROM source_rows
  ON CONFLICT (rule_set_id, rule_id, concept_id, reference_kind) DO UPDATE SET
    verification_status = EXCLUDED.verification_status,
    source_url = EXCLUDED.source_url,
    source_locator = EXCLUDED.source_locator,
    metadata = EXCLUDED.metadata;

  GET DIAGNOSTICS v_inserted = ROW_COUNT;

  IF (
    SELECT count(*)
    FROM public.rule_node_concepts rnc
    WHERE rnc.rule_set_id = v_ruleset_id
      AND (rnc.rule_id, rnc.concept_id, rnc.reference_kind) IN (
        ('round.bid', 'player-action.bid', 'defines'),
        ('scoring.bid-one-plus', 'player-action.bid', 'mentions'),
        ('resolution.mermaid-triad', 'rule-pattern.trick', 'mentions'),
        ('turn.follow-suit', 'component.special-card', 'mentions'),
        ('resolution.mermaid-triad', 'component.special-card', 'mentions'),
        ('two-player.tigress', 'component.special-card', 'modifies')
      )
      AND rnc.verification_status IN ('source_bound', 'verified')
  ) <> 6 THEN
    RAISE EXCEPTION 'Expected six source-bound Skull King concept references on the active RuleSet';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.rule_node_concepts rnc
    WHERE rnc.rule_set_id = v_ruleset_id
      AND rnc.concept_id = 'rule-pattern.trump-suit'
  ) THEN
    RAISE EXCEPTION 'Trump Suit must remain unlinked until the current RuleSet has a dedicated source-bound RuleNode';
  END IF;
END $$;

COMMIT;
