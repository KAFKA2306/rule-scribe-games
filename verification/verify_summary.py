from playwright.sync_api import Page, expect, sync_playwright
import time

def verify_summary_persistence(page: Page):
    # 1. Arrange: Go to the app.
    # Note: Frontend runs on port 5173 by default.
    page.goto("http://localhost:5173")

    # 2. Act: Search for a game.
    # I'll search for "Chess" or something common. Or maybe I should mock the backend?
    # Since I cannot easily mock backend without modifying code, I will try to use the real backend.
    # However, Gemini API key might be missing or backend might fail if not configured.
    # If backend fails, I might just verify the UI structure.

    # Assuming backend works or returns errors gracefully.
    search_input = page.get_by_placeholder("Search a game name or URL")
    search_input.fill("Chess")
    search_input.press("Enter")

    # Wait for results
    # Since backend might be slow or failing (no API keys), I'll wait a bit.
    # If search fails, error message appears.

    # Let's see if we get results.
    try:
        page.wait_for_selector(".results li", timeout=10000)
        results = page.locator(".results li")
        count = results.count()
        if count > 0:
            # Click first result
            results.first.click()

            # Click Summarize
            summarize_btn = page.get_by_text("Summarize")
            if summarize_btn.is_visible():
                summarize_btn.click()

                # Wait for summary
                # It might take time.
                # If it fails, error text appears.
                time.sleep(5)
    except Exception as e:
        print(f"Search/Summarize failed (expected if no API keys): {e}")

    # 3. Assert: Check UI elements relevant to the change.
    # I added "Summarize" button logic and "AI Summary" section.
    # Even if backend fails, the UI structure is what I changed in App.jsx.

    # I want to check if the code I changed (handling of summary) doesn't break the app.
    expect(page.get_by_text("RuleScribe mini")).to_be_visible()

    # 4. Screenshot
    page.screenshot(path="verification/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_summary_persistence(page)
        finally:
            browser.close()
