-- Bind the canonical ICE FALL record to Smart Ape Games' first-party Game Market page.
-- The legacy `icefall` record points to an unrelated game and is retired by the public visibility contract.
UPDATE games
SET identity_status = 'verified',
    identity_source = 'https://gamemarket.jp/game/184994/',
    official_url = 'https://gamemarket.jp/game/184994/',
    source_url = 'https://gamemarket.jp/game/184994/',
    source_trust = 'official_publisher',
    title = 'ICE FALL',
    title_ja = 'アイスフォール',
    title_en = 'ICE FALL',
    publisher = 'Smart Ape Games',
    min_players = 3,
    max_players = 5,
    play_time = 45,
    min_age = 10,
    published_year = 2025,
    rules_content = NULL,
    content_review_status = 'review_required',
    updated_at = NOW()
WHERE slug = 'ice-fall';
