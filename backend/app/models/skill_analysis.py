from sqlalchemy import Column, Integer, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from app.models import Base


class SkillAnalysis(Base):
    __tablename__ = "skill_analysis"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Analysis metadata
    analysis_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    jobs_analyzed = Column(Integer, nullable=True)

    # Market data - skills aggregated from all scraped jobs
    # Format: {"skill_name": {"count": int, "avg_salary": float, "frequency": float}}
    market_skills = Column(JSON, default=dict)

    # User's current skills
    # Format: ["skill1", "skill2", ...]
    user_skills = Column(JSON, default=list)

    # Skill gaps - what user is missing
    # Format: ["missing_skill1", "missing_skill2", ...]
    skill_gaps = Column(JSON, default=list)

    # AI-generated recommendations
    # Format: [{"skill": str, "priority": str, "reason": str, "learning_effort": str, "salary_impact": float}]
    recommendations = Column(JSON, default=list)

    def __repr__(self):
        return f"<SkillAnalysis(id={self.id}, user_id={self.user_id}, jobs_analyzed={self.jobs_analyzed})>"
