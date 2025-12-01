import json
import re
import logging
from typing import Any, Dict, Optional

from app.core.settings import settings

logger = logging.getLogger(__name__)

# Fallback dummy data for mock mode
MOCK_DATA = {
    "title": "Catan (Mock)",
    "description": "Catan is a multiplayer board game where players assume the roles of settlers, each attempting to build and develop holdings while trading and acquiring resources.",
    "rules_content": "**Setup**:\nPlace the board tiles. Assign resources.\n\n**Flow**:\nRoll dice, collect resources, trade, build.\n\n**Victory**:\nFirst to 10 points wins.",
    "image_url": "https://upload.wikimedia.org/wikipedia/en/a/a3/Catan-2015-boxart.jpg"
}

try:
    import google.generativeai as genai
    import httpx

    # Configure only if key is likely valid
    if settings.gemini_api_key and "PLACEHOLDER" not in settings.gemini_api_key:
        try:
            genai.configure(api_key=settings.gemini_api_key)
            HAS_GENAI = True
        except Exception as e:
            logger.warning(f"Failed to configure Gemini: {e}")
            HAS_GENAI = False
    else:
        HAS_GENAI = False

except ImportError:
    HAS_GENAI = False
    genai = None  # type: ignore
    httpx = None  # type: ignore


class GeminiClient:
    def __init__(self):
        self.is_mock = not HAS_GENAI
        if not self.is_mock:
            self.model_name = (
                settings.gemini_model
                if settings.gemini_model.startswith("models/")
                else f"models/{settings.gemini_model}"
            )
            # Use the official SDK or REST endpoint? The original code mixed them.
            # Original code used SDK for `summarize` but raw httpx for `extract_game_info`.
            # We will preserve that logic but guard it.
            self.base_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={settings.gemini_api_key}"

    async def summarize(self, context: str) -> str:
        if self.is_mock:
            return "Mock summary: Rules are simple. Have fun."

        try:
            model = genai.GenerativeModel(settings.gemini_model)
            res = await model.generate_content_async(
                f"Explain board game rules in Japanese (Markdown):\n{context}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2, max_output_tokens=512
                ),
            )
            return res.text.strip()
        except Exception as e:
            logger.error(f"Summarize failed: {e}")
            return "Failed to generate summary."

    async def extract_game_info(self, query: str) -> dict:
        if self.is_mock:
            # Return a mock result that looks like what we expect
            mock_res = MOCK_DATA.copy()
            mock_res["title"] = f"{query.capitalize()} (Mock)"
            return mock_res

        try:
            prompt = (
                f"Search official board game info for '{query}'. Prioritize official/BGG sources.\n"
                "Return JSON:\n"
                "- title: Unique name (English+Japanese e.g. 'Catan (カタン)').\n"
                "- description: Japanese summary.\n"
                "- rules_content: Detailed Japanese rules (Setup, Flow, Victory) as Markdown.\n"
                "- image_url: Official image URL.\n"
            )

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
                res.raise_for_status() # Check for 4xx/5xx
                payload = res.json()

            text = self._extract_text(payload)

            # Clean up Markdown code blocks if present
            if match := re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL):
                text = match.group(1)

            data = json.loads(text)

            # Normalize rules_content
            if isinstance(data.get("rules_content"), (dict, list)):
                rc = data["rules_content"]
                data["rules_content"] = (
                    "\n".join([f"**{k}**:\n{v}" for k, v in rc.items()])
                    if isinstance(rc, dict)
                    else "\n".join(map(str, rc))
                )
            return data

        except Exception as e:
            logger.error(f"Gemini extract failed: {e}")
            # Fallback to mock on failure to prevent 500
            return {
                "title": f"Error: {query}",
                "description": "Failed to fetch game info.",
                "rules_content": str(e),
                "image_url": ""
            }

    def _extract_text(self, payload: Dict[str, Any]) -> str:
        try:
            return payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            raise ValueError("Invalid response format from Gemini API")
