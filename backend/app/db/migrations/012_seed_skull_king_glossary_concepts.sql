BEGIN;

-- Source-bound first production use of Concept Taxonomy v1.
-- Primary source: Grandpa Beck's Games, current Skull King English rulebook,
-- Key Terms, printed page 4.
-- https://www.grandpabecksgames.com/pages/skull-king

INSERT INTO public.concepts (
  concept_id, concept_type, definition, verification_status, source_url, source_locator
)
VALUES
  (
    'rule-pattern.trick',
    'rule_pattern',
    '各プレイヤーがカードを出し、所定の順位規則で勝者を決める1回のプレイ単位。',
    'source_bound',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Current English rulebook, Key Terms, printed p.4: Trick'
  ),
  (
    'player-action.bid',
    'player_action',
    'ラウンドで自分が獲得すると予想するトリック数を宣言する行為。',
    'source_bound',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Current English rulebook, Key Terms, printed p.4: Bid'
  ),
  (
    'rule-pattern.trump-suit',
    'rule_pattern',
    '他の通常スートより高い順位を持つスート。',
    'source_bound',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Current English rulebook, Key Terms, printed p.4: Trump Suit'
  ),
  (
    'component.special-card',
    'component',
    '通常の数字付きスートカードとは異なる解決規則を持つカードの区分。',
    'source_bound',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Current English rulebook, Key Terms, printed p.4: Special Cards'
  )
ON CONFLICT (concept_id) DO UPDATE SET
  definition = EXCLUDED.definition,
  verification_status = EXCLUDED.verification_status,
  source_url = EXCLUDED.source_url,
  source_locator = EXCLUDED.source_locator,
  updated_at = now();

WITH labels(concept_id, language_code, label_type, label, normalized_label) AS (
  VALUES
    ('rule-pattern.trick', 'en', 'pref', 'Trick', 'trick'),
    ('rule-pattern.trick', 'ja', 'pref', 'トリック', 'トリック'),
    ('player-action.bid', 'en', 'pref', 'Bid', 'bid'),
    ('player-action.bid', 'ja', 'pref', 'ビッド', 'ビッド'),
    ('rule-pattern.trump-suit', 'en', 'pref', 'Trump Suit', 'trump suit'),
    ('rule-pattern.trump-suit', 'ja', 'pref', '切り札', '切り札'),
    ('component.special-card', 'en', 'pref', 'Special Card', 'special card'),
    ('component.special-card', 'ja', 'pref', '特殊カード', '特殊カード')
)
INSERT INTO public.concept_labels (concept_id, language_code, label_type, label, normalized_label)
SELECT l.concept_id, l.language_code, l.label_type, l.label, l.normalized_label
FROM labels l
WHERE NOT EXISTS (
  SELECT 1
  FROM public.concept_labels existing
  WHERE existing.concept_id = l.concept_id
    AND lower(existing.language_code) = lower(l.language_code)
    AND existing.normalized_label = l.normalized_label
);

INSERT INTO public.concept_relations (
  from_concept_id, to_concept_id, relation_type, verification_status, source_url, source_locator
)
VALUES
  (
    'player-action.bid', 'rule-pattern.trick', 'related', 'source_bound',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Current English rulebook, Overview and Key Terms, printed pp.3-4'
  ),
  (
    'rule-pattern.trump-suit', 'rule-pattern.trick', 'related', 'source_bound',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Current English rulebook, Key Terms, printed p.4'
  ),
  (
    'component.special-card', 'rule-pattern.trick', 'related', 'source_bound',
    'https://www.grandpabecksgames.com/pages/skull-king',
    'Current English rulebook, Key Terms, printed p.4'
  )
ON CONFLICT (from_concept_id, to_concept_id, relation_type) DO UPDATE SET
  verification_status = EXCLUDED.verification_status,
  source_url = EXCLUDED.source_url,
  source_locator = EXCLUDED.source_locator;

INSERT INTO public.game_concepts (
  game_id, concept_id, usage_role, verification_status, source_url, source_locator
)
SELECT
  games.id,
  seed.concept_id,
  'glossary',
  'source_bound',
  'https://www.grandpabecksgames.com/pages/skull-king',
  seed.source_locator
FROM public.games games
CROSS JOIN (
  VALUES
    ('rule-pattern.trick', 'Current English rulebook, Key Terms, printed p.4: Trick'),
    ('player-action.bid', 'Current English rulebook, Key Terms, printed p.4: Bid'),
    ('rule-pattern.trump-suit', 'Current English rulebook, Key Terms, printed p.4: Trump Suit'),
    ('component.special-card', 'Current English rulebook, Key Terms, printed p.4: Special Cards')
) AS seed(concept_id, source_locator)
WHERE games.slug = 'skull-king'
ON CONFLICT (game_id, concept_id, usage_role) DO UPDATE SET
  verification_status = EXCLUDED.verification_status,
  source_url = EXCLUDED.source_url,
  source_locator = EXCLUDED.source_locator;

COMMIT;
