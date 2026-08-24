# Public discovery must exclude records whose canonical identity is intentionally
# retired or still known to mix multiple works. Keep this list limited to active
# conflicts; repaired titles must return to normal search and mutation paths.
EXCLUDED_GAME_SLUGS = frozenset({"game"})

# `game` mixed two different games and has no single correct canonical target.
# Its two source-backed works exist separately, so public reads must not continue
# serving the contaminated historical row.
GONE_GAME_SLUGS = frozenset({"game"})


def has_known_identity_conflict(slug: str) -> bool:
    return slug in EXCLUDED_GAME_SLUGS


def should_return_gone(slug: str) -> bool:
    return slug in GONE_GAME_SLUGS


def should_hide_game_from_search(slug: str) -> bool:
    return has_known_identity_conflict(slug)
