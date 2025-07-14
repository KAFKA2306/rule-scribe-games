# rsg/tasks.py
from celery import Celery
from sqlalchemy.orm import Session
from rsg.settings import settings
from rsg.db import SessionLocal
from rsg import models, rag_pipeline

celery_app = Celery("rsg", broker=settings.celery_broker_url, backend=settings.celery_result_backend)


@celery_app.task
def generate_rule(game_id: int, title: str, raw_text: str):
    db: Session = SessionLocal()
    try:
        markdown = rag_pipeline.generate_summary(title, raw_text)
        game = db.query(models.Game).get(game_id)
        game.markdown_rules = markdown
        game.status = "COMPLETED"
        db.commit()
    except Exception as e:          # noqa
        game = db.query(models.Game).get(game_id)
        game.status = "FAILED"
        db.commit()
    finally:
        db.close()
