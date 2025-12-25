import json
import logging
import httpx
from app.core.settings import CANONICAL_GEMINI_MODEL, settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent"

    async def generate_structured_json(self, prompt: str) -> dict:
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=data,
            )

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Gemini API Error {e.response.status_code}: {e.response.text}"
            )
            raise e

        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        logger.info(f"Gemini Raw Response: {text[:200]}...")  # Log first 200 chars

        # Strip markdown if present
        if "```" in text:
            import re

            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {text}")
            raise e
