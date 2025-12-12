import json
import httpx
from app.core.settings import settings


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
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.url,
                headers={"Content-Type": "application/json"},
                params={"key": self.api_key},
                json=data,
            )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
