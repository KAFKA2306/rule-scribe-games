-- Bind the canonical `3-second-try` record to the publisher's current product page.
-- The legacy generic slug `3` is a duplicate and is retired by the public visibility contract.
UPDATE games
SET identity_status = 'verified',
    identity_source = 'https://www.itten-store.com/items/61574694',
    source_url = 'https://www.itten-store.com/items/61574694',
    source_trust = 'official_publisher',
    title = '3秒トライ！',
    title_ja = '3秒トライ！',
    title_en = '3 Second Try!',
    min_players = 2,
    max_players = 7,
    play_time = 10,
    min_age = 8,
    updated_at = NOW()
WHERE slug = '3-second-try';
