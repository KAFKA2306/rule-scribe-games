
from playwright.sync_api import sync_playwright

def verify_meta_tags():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Navigate to the file directly
        import os
        cwd = os.getcwd()
        page.goto(f"file://{cwd}/frontend/index.html")

        # Verify Title
        title = page.title()
        print(f"Title: {title}")
        if title != "ボドゲのミカタ":
            print("Title verification failed!")
            exit(1)

        # Verify Meta Description
        description = page.locator("meta[name=\"description\"]").get_attribute("content")
        print(f"Description: {description}")
        if "ボードゲームのルールを検索" not in description:
            print("Description verification failed!")
            exit(1)

        # Verify OG Title
        og_title = page.locator("meta[property=\"og:title\"]").get_attribute("content")
        print(f"OG Title: {og_title}")
        if og_title != "ボドゲのミカタ":
            print("OG Title verification failed!")
            exit(1)

        # Verify Keywords
        keywords = page.locator("meta[name=\"keywords\"]").get_attribute("content")
        print(f"Keywords: {keywords}")
        if "ボードゲーム" not in keywords:
            print("Keywords verification failed!")
            exit(1)

        # Take screenshot of the head content (not really visible but good to verify page loaded)
        page.screenshot(path="verification/verification.png")
        print("Verification successful!")

if __name__ == "__main__":
    verify_meta_tags()
