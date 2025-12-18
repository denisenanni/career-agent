from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.models import Base


class CustomSkill(Base):
    """User-contributed custom skills that aren't in job tags"""
    __tablename__ = "custom_skills"

    id = Column(Integer, primary_key=True, index=True)
    skill = Column(String, unique=True, nullable=False, index=True)
    usage_count = Column(Integer, default=1)  # How many users have this skill
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CustomSkill(skill='{self.skill}', usage_count={self.usage_count})>"
