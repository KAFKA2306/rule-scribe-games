import sys
from pathlib import Path
from mimetypes import guess_type

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.core.supabase import _client, _TABLE  # noqa: E402


BUCKET_NAME = "game-images"


def upload_images():
    print(f"Starting deployment to bucket '{BUCKET_NAME}'...")

    # Ensure bucket exists (soft check, ignoring error if exists)
    _client.storage.create_bucket(BUCKET_NAME, options={"public": True})

    # List files
    assets_dir = project_root / "frontend/public/assets/games"
    files = list(assets_dir.glob("*.png"))

    print(f"Found {len(files)} images to upload.")

    for file_path in files:
        slug = file_path.stem
        # Simple slug validation or sanitization if needed, but filenames should be slugs already

        file_bytes = file_path.read_bytes()
        mime_type = guess_type(file_path)[0] or "image/png"

        destination = f"{slug}.png"

        print(f"Uploading {slug}...")
        _client.storage.from_(BUCKET_NAME).upload(
            destination,
            file_bytes,
            file_options={"upsert": "true", "content-type": mime_type},
        )

        # Get Public URL
        public_url = _client.storage.from_(BUCKET_NAME).get_public_url(destination)

        print(f"Updating DB for {slug} -> {public_url}")

        # Update DB
        _client.table(_TABLE).update({"image_url": public_url}).eq(
            "slug", slug
        ).execute()

    print("Deployment complete.")


if __name__ == "__main__":
    upload_images()
