# rsg/gemini_client.py
import google.generativeai as genai
from rsg.settings import settings

genai.configure(api_key=settings.gemini_api_key)


class GeminiClient:
    """Google Gemini API 呼び出しラッパ"""
    def __init__(self):
        self.chat_model = genai.GenerativeModel(settings.gemini_model)
        self.embed_model = genai.GenerativeModel(settings.gemini_embed_model)

    # ---------- Embeddings ----------
    def embed(self, texts):
        res = self.embed_model.embed(content=texts)
        return [vec.values for vec in res.embedding]

    # ---------- Summaries ----------
    def summarize(self, context: str) -> str:
        system = ("あなたは国際ボードゲーム連盟公認のルール翻訳者です。"
                  "与えられた情報源のみを使い、曖昧さなく日本語で解説してください。")
        prompt = (
            "《情報源》\n"
            f"{context}\n\n"
            "《指示》\n"
            "セットアップ・ゲームの流れ・勝利条件 の3見出しを含むMarkdownを生成し、"
            "各見出しを箇条書き5行以内にまとめてください。"
            "情報源に無い事項を加えてはいけません。"
        )
        chat = self.chat_model.start_chat(history=[{"role": "system", "parts": [system]}])
        response = chat.send_message(prompt, generation_config={"temperature": 0.2, "max_output_tokens": 512})
        return response.text.strip()
