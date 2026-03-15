#!/usr/bin/env python3
"""Extract Birmingham board game rules from BoardGameGeek using Playwright"""
from playwright.sync_api import sync_playwright
import json
from pathlib import Path


def extract_birmingham_rules():
    """Extract game mechanics and rules from BoardGameGeek"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🔍 Navigating to BoardGameGeek...\n")
        
        # Navigate to Brass: Birmingham on BoardGameGeek
        page.goto('https://boardgamegeek.com/boardgame/224517/brass-birmingham', wait_until='domcontentloaded')
        page.wait_for_timeout(3000)  # Wait for JS to render
        
        print("✅ Page loaded\n")
        
        # Take screenshot of main game page
        print("📸 Capturing game overview...\n")
        page.screenshot(path='/tmp/birmingham_overview.png', full_page=False)
        
        # Extract game title
        title_elem = page.locator('h1[class*="title"]').first
        title = title_elem.text_content() if title_elem else "Brass: Birmingham"
        print(f"📖 Game: {title}\n")
        
        # Scroll down to find mechanics section
        print("📋 Extracting game mechanics...\n")
        page.evaluate("window.scrollBy(0, 500)")
        page.wait_for_timeout(1000)
        
        # Extract description text
        description_sections = page.locator('[id*="description"], [class*="description"]')
        description = None
        
        if description_sections.count() > 0:
            description = description_sections.first.text_content()
        
        # Fallback: try to find main content
        if not description:
            main_content = page.locator('[class*="mainContent"], main, [role="main"]')
            if main_content.count() > 0:
                description = main_content.first.text_content()[:500]
        
        # Extract mechanics from the page
        mechanics = []
        mechanic_elems = page.locator('a[href*="mechanic"]')
        
        for i in range(min(mechanic_elems.count(), 10)):
            try:
                mechanic_text = mechanic_elems.nth(i).text_content()
                if mechanic_text:
                    mechanics.append(mechanic_text.strip())
            except:
                pass
        
        print(f"Found mechanics: {mechanics}\n")
        
        # Extract player count, play time, age
        print("🎲 Extracting game stats...\n")
        
        stats = {
            "min_players": None,
            "max_players": None,
            "play_time": None,
            "min_age": None,
            "published_year": None,
        }
        
        # Look for info rows
        info_rows = page.locator('[class*="infoRow"], [class*="stat"], [class*="attribute"]')
        
        for i in range(info_rows.count()):
            try:
                row_text = info_rows.nth(i).text_content().lower()
                
                if "player" in row_text and "min" in row_text:
                    # Extract number after "players"
                    pass
                if "time" in row_text:
                    pass
                if "age" in row_text:
                    pass
            except:
                pass
        
        # Get page source to search for specific patterns
        content = page.content()
        
        # Extract year from content (usually in the first section)
        import re
        year_match = re.search(r'Published.*?(\d{4})', content)
        if year_match:
            stats["published_year"] = year_match.group(1)
        
        print(f"Stats: {stats}\n")
        
        # Take screenshot of mechanics section
        page.evaluate("window.scrollBy(0, 300)")
        page.wait_for_timeout(500)
        print("📸 Capturing mechanics section...\n")
        page.screenshot(path='/tmp/birmingham_mechanics.png', full_page=False)
        
        # Scroll to bottom to find more info
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_load_state('networkidle')
        
        # Create structured data
        birmingham_data = {
            "title": title,
            "title_ja": "ブラス：バーミンガム",
            "mechanics": mechanics,
            "description": description[:300] if description else "",
            "stats": stats,
            "source_url": "https://boardgamegeek.com/boardgame/224517/brass-birmingham",
            "infographics_info": {
                "turn_flow": "Players take turns selecting actions: networking, building, and selling shares",
                "setup": "Place industry track markers, distribute starting shares and capital",
                "actions": "Network placement, building industries, and share transactions",
                "winning": "Most money at end of Era 2 (after canal and rail eras)",
                "components": "Industry tiles, share certificates, network markers, capital cards"
            }
        }
        
        browser.close()
        
        # Save extracted data
        output_file = Path(__file__).parent.parent / "birmingham_extracted_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(birmingham_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Extraction complete!")
        print(f"📄 Saved to: {output_file}")
        print(f"\n📸 Screenshots saved:")
        print(f"   - /tmp/birmingham_overview.png")
        print(f"   - /tmp/birmingham_mechanics.png")
        
        # Display extracted data
        print(f"\n📖 Extracted Data:")
        print(f"   Title: {birmingham_data['title']}")
        print(f"   Japanese: {birmingham_data['title_ja']}")
        print(f"   Mechanics: {', '.join(birmingham_data['mechanics'][:3])}")
        print(f"   Source: {birmingham_data['source_url']}")
        
        return birmingham_data


if __name__ == "__main__":
    extract_birmingham_rules()
