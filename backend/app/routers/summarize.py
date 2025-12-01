from fastapi import APIRouter
from pydantic import BaseModel
from app.services.gemini_client import GeminiClient

router = APIRouter()
gemini = GeminiClient()


class SummarizeRequest(BaseModel):
    text: str


class SummarizeResponse(BaseModel):
    summary: str


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    summary = await gemini.summarize(request.text)
    return {"summary": summary}
