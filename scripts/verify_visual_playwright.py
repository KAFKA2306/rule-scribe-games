import asyncio
import os

from playwright.async_api import async_playwright


async def run():
    async with async_playwright() as p:
        # Launch browser (headless=True for CI/Background)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Navigate to Home
        print("Navigating to http://localhost:5173...")
        await page.goto("http://localhost:5173", timeout=60000)
        await page.wait_for_load_state("networkidle")

        # 2. Search for Splendor
        print("Searching for 'Splendor'...")
        try:
             await page.wait_for_selector('input[type="text"]', timeout=5000)
             await page.fill('input[type="text"]', "Splendor")
        except:
             print("Could not find input[type='text'], trying generic input...")
             await page.fill('input', "Splendor")

        # Press Enter to search
        await page.keyboard.press("Enter")

        # 3. Wait for Results
        print("Waiting for results...")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # Debug: Print page title and some content if Splendor not found
        title = await page.title()
        print(f"Page Title: {title}")

        # 4. Click first result
        print("Clicking result...")
        try:
            # Try specific link or text
            await page.click("text=Splendor", timeout=5000)
        except Exception as e:
            print(f"Click failed: {e}")
            print("Taking fallback screenshot of search results...")

        # 5. Wait for Details Page (or stay on results)
        await page.wait_for_timeout(2000)

        # 6. Screenshot
        output_path = os.path.abspath("docs/images/verification_splendor.png")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        await page.screenshot(path=output_path, full_page=True)
        print(f"Screenshot saved to: {output_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
