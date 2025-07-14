# rsg/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class GameBase(BaseModel):
    title: str


class GameCreate(GameBase):
    raw_text: str                    # 公式 PDF 抽出テキストなど


class GameResponse(GameBase):
    id: int
    status: str
    player_count: Optional[str] = None
    play_time: Optional[int] = None
    genres: Optional[List[str]] = None
    markdown_rules: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
