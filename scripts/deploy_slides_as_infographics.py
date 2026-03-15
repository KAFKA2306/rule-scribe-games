import asyncio
import os
import sys
import subprocess
import argparse

# Ensure backend directory is in path for app imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.supabase import upsert, get_by_slug

async def extract_slides_to_images(pdf_path, output_dir, prefix):
    """Convert PDF pages to PNG images using pdftocairo."""
    os.makedirs(output_dir, exist_ok=True)
    out_base = os.path.join(output_dir, prefix)
    
    print(f"📄 Converting {pdf_path} to images...")
    try:
        subprocess.run([
            "pdftocairo", "-png", pdf_path, out_base
        ], check=True)
        # pdftocairo outputs files like prefix-1.png, prefix-2.png, etc.
        files = sorted([f for f in os.listdir(output_dir) if f.startswith(prefix) and f.endswith(".png")])
        return [os.path.join(output_dir, f) for f in files]
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to convert PDF: {e}")
        return []

async def deploy_slides(slug, pdf_path):
    print(f"🚀 Deploying slides as infographics for {slug} (Japanese prioritized)...")
    
    # Verify game exists
    game = await get_by_slug(slug)
    if not game:
        print(f"✗ Game {slug} not found.")
        return

    output_dir = "frontend/public/output_slides"
    os.makedirs(output_dir, exist_ok=True)
    
    images = await extract_slides_to_images(pdf_path, output_dir, f"{slug}_slide")
    if not images:
        print("✗ No images extracted.")
        return

    # Map images to infographic keys (slide_1, slide_2, ...)
    infographics_urls = {}
    for i, img_path in enumerate(images):
        # We serve from /output_slides/ in the frontend
        filename = os.path.basename(img_path)
        url = f"/output_slides/{filename}"
        infographics_urls[f"slide_{i+1}"] = url

    # Update Supabase
    update_data = {
        "id": game["id"],
        "slug": slug,
        "title": game["title"],
        "title_ja": game["title_ja"],
        "infographics": infographics_urls
    }
    
    result = await upsert(update_data)
    if result:
        print(f"✓ Successfully updated {slug} with {len(infographics_urls)} slide infographics.")
        print(f"💡 Note: Ensure slides were generated with 'nlm slides create --language ja'")
    else:
        print(f"✗ Failed to update {slug}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--pdf", required=True)
    args = parser.parse_args()
    
    asyncio.run(deploy_slides(args.slug, args.pdf))
