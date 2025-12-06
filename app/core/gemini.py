import json
import re
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
                "temperature": 0.1,
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
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(self._clean(text))

    def _clean(self, text: str) -> str:
        if "```" in text:
            m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if m:
                return m.group(1)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        return m.group(0).strip() if m else text.strip()
