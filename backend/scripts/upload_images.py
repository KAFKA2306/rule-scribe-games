import glob
import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError as e:
    print(f"Error importing supabase client: {e}")
    sys.exit(1)
ARTIFACTS_DIR = os.path.join(
    os.environ.get("USERPROFILE", "C:\\Users\\front"),
    ".gemini",
    "antigravity",
    "brain",
    "1000671c-84be-493e-82fd-4aacc0680e14",
)
BUCKET_NAME = "images"
SLUG_MAPPING = {
    "terraforming_mars": "terraforming-mars",
    "azul_tiles": "azul",
    "blokus_pieces": "blokus",
    "scythe_mechs": "scythe",
    "viticulture_vineyard": "viticulture",
    "lost_ruins_arnak": "lost-ruins-of-arnak",
    "clank_dungeon": "clank",
    "brass_birmingham": "brass-birmingham",
    "century_spice": "century-spice-road",
    "little_town": "little-town-builders",
    "gizmos_marbles": "gizmos",
    "marrakech_rugs": "marrakech",
    "calico_cats": "calico",
    "taverns_tiefenthal": "taverns-of-tiefenthal",
    "clans_caledonia": "clans-of-caledonia",
    "web_of_power": "web-of-power",
    "fab_fib_cards": "fab-fib",
    "brass_lancashire": "brass-lancashire",
    "azul_summer": "azul-summer-pavilion",
    "for_sale_houses": "for-sale",
    "castles_ludwig": "castles-of-mad-king-ludwig",
}


def get_bucket():
    """Ensure bucket exists or return a fallback."""
    try:
        buckets = supabase.supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        target = BUCKET_NAME
        if target not in bucket_names:
            print(f"Bucket '{target}' not found. Available: {bucket_names}")
            if "games" in bucket_names:
                target = "games"
            elif "game-images" in bucket_names:
                target = "game-images"
            else:
                print(f"Attempting to create bucket '{target}'...")
                supabase.supabase.storage.create_bucket(target, {"public": True})
        return target
    except Exception as e:
        print(f"Error accessing storage: {e}")
        return BUCKET_NAME


def upload_images():
    bucket = get_bucket()
    print(f"Using bucket: {bucket}")
    png_files = glob.glob(os.path.join(ARTIFACTS_DIR, "*.png"))
    print(f"Found {len(png_files)} PNG files in artifacts dir.")
    for file_path in png_files:
        filename = os.path.basename(file_path)
        slug = None
        for key, mapped_slug in SLUG_MAPPING.items():
            if key in filename:
                slug = mapped_slug
                break
        if not slug:
            print(f"Skipping {filename}: No matching slug found.")
            continue
        print(f"Processing {slug} (from {filename})...")
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            storage_path = f"games/{slug}.png"
            content_type = "image/png"
            supabase.supabase.storage.from_(bucket).upload(
                path=storage_path, file=file_bytes, file_options={"content-type": content_type, "upsert": "true"}
            )
            public_url = supabase.supabase.storage.from_(bucket).get_public_url(storage_path)
            print(f"  Updating DB for {slug} with URL: {public_url}")
            _data, count = supabase.supabase.table("games").update({"image_url": public_url}).eq("slug", slug).execute()
            if count and count[1]:
                print("  ✅ Success!")
            else:
                print("  ⚠️ DB Update returned no modified rows? (Check if game exists)")
        except Exception as e:
            print(f"  ❌ Error uploading/updating {slug}: {e}")


if __name__ == "__main__":
    upload_images()
