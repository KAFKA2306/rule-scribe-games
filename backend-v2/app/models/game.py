"""
Game model
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Game(Base):
    """Game model"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    rules_content = Column(Text)
    player_count_min = Column(Integer)
    player_count_max = Column(Integer)
    play_time_min = Column(Integer)
    play_time_max = Column(Integer)
    complexity = Column(Float)
    year_published = Column(Integer)
    rating = Column(Float)
    genres = Column(JSON)
    mechanics = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())