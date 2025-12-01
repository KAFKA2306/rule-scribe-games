from fastapi import APIRouter, HTTPException
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
    try:
        summary = gemini.summarize(request.text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(500, str(e))
