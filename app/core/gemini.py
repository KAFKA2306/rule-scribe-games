import json
import httpx
from app.core.settings import settings


class RateLimitError(Exception):
    pass


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    async def generate_structured_json(self, prompt: str) -> dict:
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                self.url,
                headers={"Content-Type": "application/json"},
                params={"key": self.api_key},
                json=data,
            )
        if resp.status_code == 429:
            raise RateLimitError("Gemini API rate limit exceeded")
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(self._clean(text))

    def _clean(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        return text.replace("```json", "").replace("```", "").strip()
