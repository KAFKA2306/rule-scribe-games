import json
import os
import re
import httpx
from app.core.prompts import Prompts
from app.services.amazon_affiliate import amazon_search_url





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

        prompt_template = Prompts.get("gemini_client.extract_game_info")
        prompt = prompt_template.format(query=query)

        # 1. AIによる生成を実行
        result_data = await self.generate_structured_json(prompt)

        # 2. エラーでなければ、Amazonリンクを静的に注入 (Post-Processing)
        if "error" not in result_data:
            # 日本語タイトルがあればそれを優先、なければ英語タイトル、最悪の場合は検索クエリ
            search_term = (
                result_data.get("title_ja") or result_data.get("title") or query
            )

            # Master Guideの方針に従い、検索結果ページへのリンクを生成
            affiliate_link = amazon_search_url(search_term)

            if affiliate_link:
                result_data["amazon_url"] = affiliate_link

        return result_data

    async def generate_structured_json(self, prompt: str) -> dict:
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        # 将来的にはここに tools: [{google_search: {}}] を追加すると精度がさらに向上します
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient() as client:
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
