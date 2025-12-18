import json
import httpx
from app.core.settings import CANONICAL_GEMINI_MODEL, settings


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        if self.model != CANONICAL_GEMINI_MODEL:
            raise ValueError(
                f"Gemini model must be exactly `{CANONICAL_GEMINI_MODEL}` "
                f"(got `{self.model}`)."
            )
        self.url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent"

    async def generate_structured_json(self, prompt: str) -> dict:
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=data,
            )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
