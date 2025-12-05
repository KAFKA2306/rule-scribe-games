import json
import re
import asyncio
import httpx
from app.core.settings import settings

_RETRY_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 5
_INITIAL_BACKOFF = 2.0
_HTTP_TIMEOUT = 300.0


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent"
        self.last_attempts = 0

    async def _post_with_retry(self, json_payload: dict) -> httpx.Response:
        backoff = _INITIAL_BACKOFF
        attempts = 0
        for attempt in range(1, _MAX_RETRIES + 1):
            attempts = attempt
            try:
                async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                    resp = await client.post(
                        self.base_url,
                        headers={"Content-Type": "application/json"},
                        params={"key": self.api_key},
                        json=json_payload,
                    )
                if resp.status_code in _RETRY_STATUS:
                    if attempt == _MAX_RETRIES:
                        return resp
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                self.last_attempts = attempts
                return resp
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                if attempt == _MAX_RETRIES:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2
        self.last_attempts = attempts
        return resp  # fallback (should not reach)

    async def generate_structured_json(self, prompt: str) -> dict:
        self.last_attempts = 0
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            # Tools disabled to allow application/json responses reliably.
            "tools": [],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }
        response = await self._post_with_retry(data)
        # store attempts if available
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
        # fallback: grab first {...} block
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            return brace_match.group(0).strip()
        return text.strip()
