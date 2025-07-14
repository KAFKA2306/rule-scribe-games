# rsg/api.py
import json
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from rsg.db import get_db, engine
from rsg import models, schemas
from rsg.tasks import generate_rule

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Rule-Scribe-Games API (Gemini)")

# ------------------ 検索 ------------------
@app.get("/search", response_model=List[schemas.GameResponse])
def search(q: str, db: Session = Depends(get_db)):
    games = (
        db.query(models.Game)
        .filter(models.Game.title.contains(q))
        .filter(models.Game.status == "COMPLETED")
        .all()
    )
    return [
        schemas.GameResponse(
            id=g.id,
            title=g.title,
            status=g.status,
            player_count=g.player_count,
            play_time=g.play_time,
            genres=json.loads(g.genres) if g.genres else None,
            markdown_rules=g.markdown_rules,
            created_at=g.created_at,
        )
        for g in games
    ]


# ------------------ 生成リクエスト ---------
@app.post("/request", response_model=schemas.GameResponse)
def request_rule(data: schemas.GameCreate, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter_by(title=data.title).first()
    if game:
        return schemas.GameResponse.from_orm(game)

    # 新規登録
    game = models.Game(title=data.title, status="PROCESSING")
    db.add(game)
    db.commit()
    db.refresh(game)

    # Celery タスクキュー
    generate_rule.delay(game.id, data.title, data.raw_text)
    return schemas.GameResponse.from_orm(game)


# ------------------ 単一ゲーム取得 ---------
@app.get("/games/{game_id}", response_model=schemas.GameResponse)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).get(game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    return schemas.GameResponse.from_orm(game)
