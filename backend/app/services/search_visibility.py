# Public discovery must exclude records whose canonical identity is intentionally
# retired or still known to mix multiple works. Keep this list limited to active
# conflicts; repaired titles must return to normal search and mutation paths.
EXCLUDED_GAME_SLUGS = frozenset({
    "game",
    "hackclad",
    "3",
    "little-town-builders",
    "heart-of-crown",
    "icefall",
})

# `game` mixed two different games and has no single correct canonical target.
# `hackclad` is a superseded duplicate of the verified `hack-clad` canonical work.
# `3` is a superseded duplicate of the source-backed `3-second-try` work.
# `little-town-builders` is a superseded duplicate of verified `little-town`.
# `heart-of-crown` duplicates the explicitly edition-scoped `heart-of-crown-2nd-edition` record.
# `icefall` points to an unrelated Game Market product and duplicates the repaired `ice-fall` title.
# Public reads must not continue serving retired records as canonical content.
GONE_GAME_SLUGS = frozenset({
    "game",
    "hackclad",
    "3",
    "little-town-builders",
    "heart-of-crown",
    "icefall",
})


def has_known_identity_conflict(slug: str) -> bool:
    return slug in EXCLUDED_GAME_SLUGS


def should_return_gone(slug: str) -> bool:
    return slug in GONE_GAME_SLUGS


def game_indexability(game: dict) -> tuple[bool, tuple[str, ...]]:
    """Return one fail-closed indexability decision shared by SSR and sitemap.

    A catalog row is not search-release-ready merely because it exists. Keep
    review-required, AI-draft, unknown-review and unverified identities publicly
    readable when appropriate, but out of search indexing until reviewed.
    """
    reasons: list[str] = []
    slug = str(game.get("slug") or "").strip()
    if not slug:
        reasons.append("missing_slug")
    elif has_known_identity_conflict(slug):
        reasons.append("identity_conflict")

    if game.get("identity_status") != "verified":
        reasons.append("identity_not_verified")
    if game.get("content_review_status") != "human_reviewed":
        reasons.append("content_not_human_reviewed")

    return not reasons, tuple(reasons)


def should_hide_game_from_search(game_or_slug: dict | str) -> bool:
    if isinstance(game_or_slug, dict):
        indexable, _ = game_indexability(game_or_slug)
        return not indexable
    return has_known_identity_conflict(game_or_slug)
