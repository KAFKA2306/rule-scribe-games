# rsg/rag_pipeline.py
from typing import List
from qdrant_client import QdrantClient, models as qdrant
from rsg.settings import settings
from rsg.embeddings import embed_texts
from rsg.gemini_client import GeminiClient

client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
gemini = GeminiClient()


def ensure_collection():
    if settings.collection_name not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=qdrant.VectorParams(size=settings.vector_dim, distance=qdrant.Distance.COSINE),
        )


ensure_collection()


def chunk(text: str, size: int = 1000, overlap: int = 200) -> List[str]:
    words = text.split()
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, len(words), step)]


def index_document(game_id: int, text: str) -> None:
    splits = chunk(text)
    vectors = embed_texts(splits)
    payloads = [{"game_id": game_id, "chunk": c} for c in splits]
    client.upsert(
        settings.collection_name,
        qdrant.Batch(ids=list(range(len(splits))), vectors=vectors, payloads=payloads),
    )


def retrieve(title: str, top_k: int = 5) -> str:
    vec = embed_texts([title])[0]
    hits = client.search(settings.collection_name, query_vector=vec, limit=top_k)
    return "\n".join(h.payload["chunk"] for h in hits)


def generate_summary(title: str, text: str) -> str:
    index_document(0, text)            # game_id=0 は暫定
    context = retrieve(title)
    return gemini.summarize(context)
