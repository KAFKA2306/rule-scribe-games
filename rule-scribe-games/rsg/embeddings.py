# rsg/embeddings.py
from typing import List
from rsg.gemini_client import GeminiClient

_client = GeminiClient()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Gemini Embedding API"""
    return _client.embed(texts)
