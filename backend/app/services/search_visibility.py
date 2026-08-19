# These records are known to mix fields from different game identities.
# Keep them out of search indexing until the underlying records are repaired.
EXCLUDED_GAME_SLUGS = frozenset({"game", "hack-clad"})


def should_hide_game_from_search(slug: str) -> bool:
    return slug in EXCLUDED_GAME_SLUGS
