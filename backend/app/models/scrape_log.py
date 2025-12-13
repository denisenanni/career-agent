"""Scrape log model"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.models import Base


class ScrapeLog(Base):
    """Model for tracking scrape operations"""

    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    status = Column(String(50), default="running")
    error = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ScrapeLog(id={self.id}, source={self.source}, status={self.status})>"
