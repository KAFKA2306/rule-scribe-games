import json
import re
from typing import Any, Dict

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - environment may lack the SDK on Vercel
    genai = None  # type: ignore

from app.core.settings import settings
import httpx

if genai is not None and "PLACEHOLDER" not in settings.gemini_api_key:
    try:
        genai.configure(api_key=settings.gemini_api_key)
    except Exception:
        # Fall through to mock mode if configure fails (e.g., invalid key/runtime)
        genai = None


class GeminiClient:
    def __init__(self):
        self.is_mock = genai is None or "PLACEHOLDER" in settings.gemini_api_key
        if not self.is_mock:
            self.model_name = (
                settings.gemini_model
                if settings.gemini_model.startswith("models/")
                else f"models/{settings.gemini_model}"
            )
            self.base_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={settings.gemini_api_key}"

    async def summarize(self, context: str) -> str:
        if self.is_mock:
            return "This is a mock summary. Please configure a valid GEMINI_API_KEY in backend/.env to get real AI-powered summaries."

        try:
            model = genai.GenerativeModel(settings.gemini_model)
            res = await model.generate_content_async(
                f"Explain board game rules in Japanese (Markdown):\n{context}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2, max_output_tokens=512
                ),
            )
            return res.text.strip()
        except Exception as exc:
            return f"サマリー生成に失敗しました（{exc}）。時間を置いて再試行してください。"

    async def extract_game_info(self, query: str) -> dict:
        if self.is_mock:
            return {
                "title": f"Mock Game: {query}",
                "description": "This is a mock result because the API key is not configured.",
                "rules_content": "# Mock Rules\n\n1. Setup the game.\n2. Play turns.\n3. Win.\n\n**Note**: Configure `GEMINI_API_KEY` in `backend/.env` for real results.",
                "image_url": "https://placehold.co/600x400?text=Mock+Game"
            }

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
                res.raise_for_status()
                payload = res.json()
        except Exception as exc:  # network, auth, JSON errors
            return self._fallback(query, reason=str(exc))

        text = self._extract_text(payload)
        if not text:
            return self._fallback(query, reason="empty candidates")

        if match := re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL):
            text = match.group(1)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return self._fallback(query, reason=f"parse error: {exc}")

        if isinstance(data.get("rules_content"), (dict, list)):
            rc = data["rules_content"]
            data["rules_content"] = (
                "\n".join([f"**{k}**:\n{v}" for k, v in rc.items()])
                if isinstance(rc, dict)
                else "\n".join(map(str, rc))
            )
        return data

    def _extract_text(self, payload: Dict[str, Any]) -> str | None:
        try:
            candidates = payload["candidates"]
            if not candidates:
                return None
            return candidates[0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            return None

    def _fallback(self, query: str, reason: str) -> Dict[str, str]:
        """
        Guaranteed-safe structure so that upstream can still upsert without crashing.
        """
        return {
            "title": f"暫定タイトル: {query}",
            "description": f"自動取得に失敗しました（{reason}）。入力内容を確認してください。",
            "rules_content": "取得に失敗しました。手動でルールを追加してください。",
            "image_url": None,
        }
