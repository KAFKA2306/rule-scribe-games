-- Public game pages must not retain user-supplied replay provenance.
-- Official Board Game Arena rule pages remain allowed; only archive/replay URLs
-- and the internal marker for user-supplied replay logs are rejected.

ALTER TABLE public.games
    DROP CONSTRAINT IF EXISTS games_no_user_replay_provenance;

ALTER TABLE public.games
    ADD CONSTRAINT games_no_user_replay_provenance
    CHECK (
        COALESCE(rules_content, '') NOT ILIKE '%boardgamearena.com/archive/replay/%'
        AND COALESCE(rules_content, '') NOT ILIKE '%ユーザー提供リプレイログ%'
        AND COALESCE(structured_data::text, '') NOT ILIKE '%user_supplied_replay_log%'
        AND COALESCE(structured_data::text, '') NOT ILIKE '%boardgamearena.com/archive/replay/%'
    );
