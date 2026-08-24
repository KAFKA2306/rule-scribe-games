# Public discovery must exclude records whose canonical identity is intentionally
# retired or still known to mix multiple works. Keep this list limited to active
# conflicts; repaired titles must return to normal search and mutation paths.
EXCLUDED_GAME_SLUGS = frozenset({"game", "hackclad", "3"})

# `game` mixed two different games and has no single correct canonical target.
# `hackclad` is a superseded duplicate of the verified `hack-clad` canonical work.
# `3` is a superseded duplicate of the source-backed `3-second-try` work.
# Public reads must not continue serving retired records as canonical content.
GONE_GAME_SLUGS = frozenset({"game", "hackclad", "3"})


def has_known_identity_conflict(slug: str) -> bool:
    return slug in EXCLUDED_GAME_SLUGS


def should_return_gone(slug: str) -> bool:
    return slug in GONE_GAME_SLUGS


def should_hide_game_from_search(slug: str) -> bool:
    return has_known_identity_conflict(slug)
