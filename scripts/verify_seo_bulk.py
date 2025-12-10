import requests
import sys
import xml.etree.ElementTree as ET

# Base URL to verify
BASE_URL = "https://bodoge-no-mikata.vercel.app"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

def verify_game_seo(url):
    print(f"Checking {url}...", end=" ", flush=True)
    try:
        r = requests.get(url, timeout=10)
        content = r.text
        
        # Checks
        has_title_suffix = "| ボドゲのミカタ" in content
        # We look for the game specific title part, but generic check is handled by the suffix existing in <title>
        # A bit loose, but verifies injection happened vs generic "Vite + React" or old title.
        
        has_json_ld = '<script type="application/ld+json">' in content
        # Specifically check for "Game" type to distinguish from site-wide json-ld
        has_game_schema = '"@type": "Game"' in content or '"@type":"Game"' in content
        
        has_og_image = 'content="https://bodoge-no-mikata.vercel.app/og-image.png"' not in content and 'property="og:image"' in content
        # Note: If image is missing, it falls back to og-image.png in our logic? 
        # Actually our logic in seo_renderer.py:
        # if not image_url: image_url = ...og-image.png
        # So verifying it's NOT the default might fail if game has no image.
        # Better check: Does it have the dynamically injected tags?
        
        if has_title_suffix and has_game_schema:
            print("✅ OK")
            return True
        else:
            print("❌ FAIL")
            if not has_title_suffix: print(f"  - Missing Title Suffix (got: {content[content.find('<title>'):content.find('</title>')+8]})")
            if not has_game_schema: print("  - Missing Game JSON-LD")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print(f"Fetching sitemap from {SITEMAP_URL}...")
    try:
        r = requests.get(SITEMAP_URL)
        root = ET.fromstring(r.text)
        
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [url.find('sm:loc', ns).text for url in root.findall('sm:url', ns)]
        
        game_urls = [u for u in urls if '/games/' in u]
        print(f"Found {len(game_urls)} game URLs.")
        
        success_count = 0
        for url in game_urls:
            if verify_game_seo(url):
                success_count += 1
                
        print(f"\nSummary: {success_count}/{len(game_urls)} passed.")
        
    except Exception as e:
        print(f"Failed to process sitemap: {e}")

if __name__ == "__main__":
    main()
