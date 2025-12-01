from playwright.sync_api import Page, expect, sync_playwright

def verify_summary_persistence(page: Page):
    # Log console messages
    page.on("console", lambda msg: print(f"Console: {msg.text}"))
    page.on("requestfailed", lambda request: print(f"Request failed: {request.url} {request.failure}"))

    # Mock /api/search
    page.route("**/api/search", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": 1, "title": "Mock Game", "description": "A mock game.", "rules_content": "These are the rules.", "summary": "Existing summary."}]'
    ))

    # Mock /api/summarize
    page.route("**/api/summarize", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"summary": "Generated summary."}'
    ))

    page.goto("http://localhost:5173")

    # Act: Search
    search_input = page.get_by_placeholder("Search a game name or URL")
    search_input.fill("Mock Game")
    search_input.press("Enter")

    # Wait for results
    try:
        page.wait_for_selector(".results li", timeout=5000)
    except Exception:
        print("Timed out waiting for results. Taking screenshot for debug.")
        page.screenshot(path="verification/debug.png")
        raise

    # Verify result has summary initially (because I mocked it in search response)
    results = page.locator(".results li")
    results.first.click()

    # Check if "Summarized" button is disabled and text is "Summarized"
    # And "AI Summary" section is visible
    expect(page.get_by_text("Summarized")).to_be_visible()
    expect(page.get_by_text("AI Summary")).to_be_visible()
    expect(page.get_by_text("Existing summary.")).to_be_visible()

    # Now let's try a case without summary
    page.route("**/api/search", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": 2, "title": "New Game", "description": "New game desc.", "rules_content": "New rules.", "summary": null}]'
    ))

    # Clear and search again
    page.get_by_text("Clear").click()
    search_input.fill("New Game")
    search_input.press("Enter")

    page.wait_for_selector(".results li")
    results.first.click()

    # Should see "Summarize" button (not "Summarized")
    expect(page.get_by_text("Summarize", exact=True)).to_be_visible()
    expect(page.get_by_text("AI Summary")).not_to_be_visible()

    # Click Summarize
    page.get_by_text("Summarize").click()

    # Should see summary appear
    expect(page.get_by_text("Generated summary.")).to_be_visible()
    expect(page.get_by_text("Summarized")).to_be_visible()

    # Screenshot
    page.screenshot(path="verification/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_summary_persistence(page)
        finally:
            browser.close()
