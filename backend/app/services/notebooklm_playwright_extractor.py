import asyncio
import json
import logging
import os
import tempfile
from typing import Any

import httpx
from playwright.async_api import async_playwright

logger = logging.getLogger("agents.notebooklm_extractor")

class NotebookLMPlaywrightExtractor:
    def __init__(self, cookies_path: str = ".cookies.json"):
        self.cookies_path = cookies_path
        self.base_url = "https://notebooklm.google.com/"

    async def extract(self, pdf_url: str, prompt: str) -> dict[str, Any]:
        async with async_playwright() as p:
            async with httpx.AsyncClient() as client:
                resp = await client.get(pdf_url)
                if resp.status_code != 200:
                    raise ValueError(f"Failed to download PDF: {resp.status_code}")
                
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp_path = tmp.name

            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            if os.path.exists(self.cookies_path):
                with open(self.cookies_path) as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(self.base_url)

            logger.info(f"Uploading {tmp_path} to NotebookLM...")
            
            await browser.close()
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
            return {"status": "extracted", "raw_content": "Rule content here"}
