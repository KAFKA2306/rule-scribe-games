-- Public game pages must not retain user-supplied replay provenance.
-- Official Board Game Arena rule pages remain allowed. Replay URLs, replay-log
-- markers, table identifiers, and player identifiers are rejected.

ALTER TABLE public.games
    DROP CONSTRAINT IF EXISTS games_no_user_replay_provenance;

ALTER TABLE public.games
    ADD CONSTRAINT games_no_user_replay_provenance
    CHECK (
        COALESCE(rules_content, '') NOT ILIKE '%boardgamearena.com/archive/replay/%'
        AND COALESCE(rules_content, '') NOT ILIKE '%ユーザー提供リプレイログ%'
        AND COALESCE(rules_content, '') !~ 'BGAテーブル[[:space:]]*#?[0-9]+'
        AND COALESCE(structured_data::text, '') NOT ILIKE '%user_supplied_replay_log%'
        AND COALESCE(structured_data::text, '') NOT ILIKE '%boardgamearena.com/archive/replay/%'
        AND COALESCE(structured_data::text, '') !~* '"(table_id|player_id)"[[:space:]]*:'
    );
