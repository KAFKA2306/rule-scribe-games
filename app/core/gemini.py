import json
import re

import httpx
from app.core.settings import settings


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent"
        self.last_attempts = 0

    async def _post_no_retry(self, json_payload: dict) -> httpx.Response:
        async with httpx.AsyncClient(timeout=300.0) as client:
            return await client.post(
                self.base_url,
                headers={"Content-Type": "application/json"},
                params={"key": self.api_key},
                json=json_payload,
            )

    async def generate_structured_json(self, prompt: str) -> dict:
        self.last_attempts = 0

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }
        response = await self._post_no_retry(data)

        if hasattr(self, "last_attempts"):
            self.last_attempts = getattr(self, "last_attempts", 0) or 1
        else:
            self.last_attempts = 1
        response.raise_for_status()
        result = response.json()
        text_content = result["candidates"][0]["content"]["parts"][0]["text"]
        cleaned_text = self._clean_json_string(text_content)
        return json.loads(cleaned_text)

    def _clean_json_string(self, text: str) -> str:
        if "```" in text:
            match = re.search("```(?:json)?\\s*(.*?)\\s*```", text, re.DOTALL)
            if match:
                return match.group(1)

        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            return brace_match.group(0).strip()
        return text.strip()
