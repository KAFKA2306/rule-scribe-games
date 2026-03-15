import json
import logging
import re
from typing import Any

import httpx

from app.core.settings import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent"

    async def generate_structured_json(self, prompt: str, api_key: str | None = None) -> dict[str, Any]:
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        }
        key = api_key or self.api_key
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": key,
                },
                json=data,
            )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        logger.info(f"Gemini Raw Response: {text[:200]}...")
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        return json.loads(text)
