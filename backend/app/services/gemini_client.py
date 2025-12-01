import google.generativeai as genai
from app.core.settings import settings
import requests
import json

genai.configure(api_key=settings.gemini_api_key)


class GeminiClient:
    def __init__(self):
        self.model_name = (
            settings.gemini_model
            if settings.gemini_model.startswith("models/")
            else f"models/{settings.gemini_model}"
        )
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={settings.gemini_api_key}"

    def summarize(self, context: str) -> str:
        model = genai.GenerativeModel(settings.gemini_model)
        res = model.generate_content(
            f"Explain board game rules in Japanese (Markdown):\n{context}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.2, max_output_tokens=512
            ),
        )
        return res.text.strip()

    def extract_game_info(self, query: str) -> dict:
        prompt = (
            f"Search official board game info for '{query}'. Prioritize official/BGG sources.\n"
            "Return JSON:\n"
            "- title: Unique name (English+Japanese e.g. 'Catan (カタン)').\n"
            "- description: Japanese summary.\n"
            "- rules_content: Detailed Japanese rules (Setup, Flow, Victory) as Markdown.\n"
            "- image_url: Official image URL.\n"
        )
        res = requests.post(
            self.base_url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
            },
        )
        res.raise_for_status()
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
        data = json.loads(text)

        if isinstance(data.get("rules_content"), (dict, list)):
            rc = data["rules_content"]
            data["rules_content"] = (
                "\n".join([f"**{k}**:\n{v}" for k, v in rc.items()])
                if isinstance(rc, dict)
                else "\n".join(map(str, rc))
            )
        return data
