# These records are known to mix fields from different game identities.
# Keep them out of search indexing and block normal mutation until the
# underlying records are repaired through an explicit reviewed workflow.
EXCLUDED_GAME_SLUGS = frozenset({"game", "hack-clad"})


def has_known_identity_conflict(slug: str) -> bool:
    return slug in EXCLUDED_GAME_SLUGS


def should_hide_game_from_search(slug: str) -> bool:
    return has_known_identity_conflict(slug)
