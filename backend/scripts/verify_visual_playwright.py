import asyncio
import os

from playwright.async_api import async_playwright


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://localhost:5173")
        await page.wait_for_load_state("networkidle")

        await page.wait_for_selector('input[type="text"]')
        await page.fill('input[type="text"]', "Splendor")
        await page.keyboard.press("Enter")

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        await page.click("text=Splendor")
        await page.wait_for_timeout(2000)

        output_path = os.path.abspath("docs/images/verification_splendor.png")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        await page.screenshot(path=output_path, full_page=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
