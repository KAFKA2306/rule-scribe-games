import json
import os
import re
import httpx


class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")

        self.model_name = "gemini-2.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    async def extract_game_info(self, query: str) -> dict:
        if not self.api_key:
            return {"error": "Gemini API key not configured"}

        prompt = f"""
        You are a board game database expert.
        Search for the board game "{query}" and generate a JSON object with the following fields.
        Do not include any markdown formatting, explanations, or code blocks. Return ONLY the raw JSON string.

        Required Fields:
        - title: (string) Official title
        - title_ja: (string) Japanese title (if available, else same as title)
        - title_en: (string) English title
        - description: (string) Brief description (Japanese)
        - rules_content: (string) Detailed complete rules for real play (Japanese). Include setup, turn structure, and victory conditions.
        - image_url: (string) URL to a box art image (use a placeholder if not found)
        - min_players: (integer)
        - max_players: (integer)
        - play_time: (integer) Minutes
        - min_age: (integer) Years
        - published_year: (integer)
        - official_url: (string or null)
        - bgg_url: (string or null)
        - structured_data: {{
            "keywords": [{{"term": "string", "description": "string"}}],
            "popular_cards": []
        }}

        If the game is not found, return an error JSON: {{"error": "Game not found"}}
        """

        return await self.generate_structured_json(prompt)

    async def generate_structured_json(self, prompt: str) -> dict:
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url, headers=headers, params=params, json=data
                )
                response.raise_for_status()

                result = response.json()
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]

                cleaned_text = self._clean_json_string(text_content)

                return json.loads(cleaned_text)

        except httpx.HTTPStatusError as e:
            print(f"Gemini API HTTP Error: {e}")
            return {"error": f"Gemini API request failed: {e.response.text}"}
        except httpx.RequestError as e:
            print(f"Gemini API Request Error: {e}")
            return {"error": f"Gemini API connection failed: {str(e)}"}
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Gemini Response Parsing Error: {e}")
            return {"error": "Failed to parse Gemini response"}

    def _clean_json_string(self, text: str) -> str:
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                return match.group(1)
        return text.strip()
