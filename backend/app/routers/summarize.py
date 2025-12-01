from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.gemini_client import GeminiClient
from app.core.supabase import supabase_repository

router = APIRouter()
gemini = GeminiClient()


class SummarizeRequest(BaseModel):
    text: str
    game_id: Optional[int] = None


class SummarizeResponse(BaseModel):
    summary: str


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    if request.game_id:
        game = await supabase_repository.get_by_id(request.game_id)
        if game and game.get("summary"):
            return {"summary": game["summary"]}

    summary = await gemini.summarize(request.text)

    if request.game_id:
        await supabase_repository.update_summary(request.game_id, summary)

    return {"summary": summary}
