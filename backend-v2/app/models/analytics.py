"""
Analytics model
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base


class SearchAnalytics(Base):
    """Search analytics model"""
    __tablename__ = "search_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    query = Column(Text, nullable=False)
    results_count = Column(Integer)
    processing_time_ms = Column(Float)
    search_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())