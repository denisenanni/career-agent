from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON
from datetime import datetime, timezone
from app.models import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)

    # Match score (0-100)
    score = Column(Float, nullable=False, index=True)

    # AI analysis
    analysis = Column(Text, nullable=True)  # Why this is a good match
    reasoning = Column(JSON, nullable=True)  # Structured reasoning

    # Application tracking
    status = Column(String, default="matched", index=True)  # matched, interested, applied, rejected
    applied_at = Column(DateTime, nullable=True)

    # Generated content
    cover_letter = Column(Text, nullable=True)
    cv_highlights = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Match(id={self.id}, user_id={self.user_id}, job_id={self.job_id}, score={self.score})>"
