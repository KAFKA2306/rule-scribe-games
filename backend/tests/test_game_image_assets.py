from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GAME_IMAGE_DIR = REPOSITORY_ROOT / "frontend" / "public" / "images" / "games"


def test_repository_managed_game_images_are_webp_only():
    image_files = sorted(path for path in GAME_IMAGE_DIR.iterdir() if path.is_file())
    assert image_files, "Expected repository-managed game images"

    non_webp = [path.name for path in image_files if path.suffix.lower() != ".webp"]
    assert non_webp == [], f"Repository-managed game images must be WebP: {non_webp}"
