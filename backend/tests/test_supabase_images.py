from app.core import supabase


def test_audited_placeholder_uses_public_storage_url(monkeypatch):
    monkeypatch.setattr(supabase.settings, "supabase_url", "https://example.supabase.co")
    game = {"slug": "splendor", "image_url": "https://via.placeholder.com/400x300?text=Splendor"}
    normalized = supabase._with_canonical_storage_image(game)
    assert normalized["image_url"] == "https://example.supabase.co/storage/v1/object/public/game-images/splendor.png"
    assert game["image_url"].startswith("https://via.placeholder.com/")


def test_audited_legacy_local_url_uses_public_storage_url(monkeypatch):
    monkeypatch.setattr(supabase.settings, "supabase_url", "https://example.supabase.co/")
    game = {"slug": "yokohama-duel", "image_url": "/assets/games/yokohama-duel.webp"}
    normalized = supabase._with_canonical_storage_image(game)
    assert normalized["image_url"] == "https://example.supabase.co/storage/v1/object/public/game-images/yokohama-duel.png"


def test_missing_or_unaudited_image_is_not_inferred(monkeypatch):
    monkeypatch.setattr(supabase.settings, "supabase_url", "https://example.supabase.co")
    game = {"slug": "modern-art", "image_url": None}
    assert supabase._with_canonical_storage_image(game) is game
