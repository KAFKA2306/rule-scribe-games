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

    async def extract_game_info(self, query: str) -> dict:
        prompt = (
            f"User Query: '{query}'\n\n"
            "Task: Search for official board game info or update existing game data based on the query.\n"
            "If the query implies updating (e.g. 'add card list', 'update rules'), find the game and apply changes.\n"
            "Prioritize official/BGG sources.\n\n"
            "Return JSON:\n"
            "- title: Unique name (English+Japanese e.g. 'Catan (カタン)').\n"
            "- description: Japanese summary.\n"
            "- rules_content: Detailed Japanese rules (Setup, Flow, Victory) as Markdown.\n"
            "- image_url: Official image URL.\n"
            "- structured_data: JSON object with:\n"
            "  - keywords: List of {term, description} (key mechanics/terms).\n"
            "  - popular_cards: List of {name, type, cost, reason} (key cards/components).\n"
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
                    print(f"Gemini API Error {res.status_code}: {res.text}")
                    # Return error dict that frontend can handle
                    return {"error": f"API Error {res.status_code}"}

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
            return {"error": str(e)}

    def _extract_text(self, payload: Dict[str, Any]) -> str:
        try:
            return payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            raise ValueError("Invalid response format from Gemini API")

    async def generate_structured_json(self, prompt: str) -> dict:
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
