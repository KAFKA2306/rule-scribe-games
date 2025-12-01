import json
import re
from typing import Any, Dict

import httpx

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from app.core.settings import settings, PLACEHOLDER

# Configure genai if available and key is valid
if genai and settings.gemini_api_key and settings.gemini_api_key != PLACEHOLDER:
    try:
        genai.configure(api_key=settings.gemini_api_key)
    except Exception:
        pass


class GeminiClient:
    def __init__(self):
        self.model_name = (
            settings.gemini_model
            if settings.gemini_model.startswith("models/")
            else f"models/{settings.gemini_model}"
        )
        # Use key if available, otherwise empty string (will fail if used against real API)
        key = settings.gemini_api_key if settings.gemini_api_key != PLACEHOLDER else ""
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={key}"

    @property
    def is_mock(self) -> bool:
        return (
            genai is None
            or not settings.gemini_api_key
            or settings.gemini_api_key == PLACEHOLDER
        )

    async def summarize(self, context: str) -> str:
        if self.is_mock:
            return "Summary unavailable (Backend running in Mock Mode - No Gemini API Key configured)."

        try:
            model = genai.GenerativeModel(settings.gemini_model)
            res = await model.generate_content_async(
                f"Explain board game rules in Japanese (Markdown):\n{context}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2, max_output_tokens=512
                ),
            )
            return res.text.strip()
        except Exception:
            return "Failed to generate summary."

    async def extract_game_info(self, query: str) -> dict:
        if self.is_mock:
            return self._mock_response(query)

        prompt = (
            f"Search official board game info for '{query}'. Prioritize official/BGG sources.\n"
            "Return JSON:\n"
            "- title: Unique name (English+Japanese e.g. 'Catan (カタン)').\n"
            "- description: Japanese summary.\n"
            "- rules_content: Detailed Japanese rules (Setup, Flow, Victory) as Markdown.\n"
            "- image_url: Official image URL.\n"
        )

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    self.base_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "tools": [{"google_search": {}}],
                    },
                    timeout=30.0,
                )

                if res.status_code != 200:
                    # Fallback to mock if API fails
                    print(f"Gemini API Error {res.status_code}: {res.text}")
                    return self._mock_response(
                        query, error=f"API Error {res.status_code}"
                    )

                payload = res.json()

            text = self._extract_text(payload)
            if match := re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL):
                text = match.group(1)

            data = json.loads(text)

            # Normalize rules_content to string if it came back as dict/list
            if isinstance(data.get("rules_content"), (dict, list)):
                rc = data["rules_content"]
                data["rules_content"] = (
                    "\n".join([f"**{k}**:\n{v}" for k, v in rc.items()])
                    if isinstance(rc, dict)
                    else "\n".join(map(str, rc))
                )
            return data

        except Exception as e:
            print(f"Gemini extraction failed: {e}")
            return self._mock_response(query, error=str(e))

    def _extract_text(self, payload: Dict[str, Any]) -> str:
        try:
            return payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            raise ValueError("Invalid response format from Gemini API")

    def _mock_response(self, query: str, error: str = "") -> dict:
        description = "This is a mock description because the backend is running in safe mode without a valid Gemini API Key."
        if error:
            description += f" (Error: {error})"

        return {
            "title": f"Mock Game: {query}",
            "description": description,
            "rules_content": "## Mock Rules\n\n1. **Setup**: None required.\n2. **Play**: Imagine the game.\n3. **Win**: Everyone wins in mock mode.",
            "image_url": "https://placehold.co/600x400?text=Mock+Game",
            "source_url": "mock://system",
        }

    async def generate_structured_json(self, prompt: str) -> dict:
        if self.is_mock:
            return {"type": "unknown", "overview": "Mock data"}

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    self.base_url,
                    headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=30.0,
                )

                if res.status_code != 200:
                    return {}

                payload = res.json()
                text = self._extract_text(payload)

                if match := re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL):
                    text = match.group(1)

                return json.loads(text)

        except Exception as e:
            print(f"Structured JSON generation failed: {e}")
            return {}
