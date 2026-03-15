from playwright.sync_api import sync_playwright
import sys

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    
    print("✓ Chrome opened. Press Ctrl+C to close...")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing browser...")
        browser.close()
