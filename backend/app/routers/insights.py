"""
Insights router - career insights and skill analysis
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import User, SkillAnalysis
from app.dependencies.auth import get_current_user
from app.services.insights import run_skill_analysis_for_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


# Pydantic schemas
class SkillRecommendation(BaseModel):
    skill: str
    priority: str
    reason: str
    frequency: float
    salary_impact: Optional[float]
    learning_effort: str


class SkillAnalysisResponse(BaseModel):
    user_skills: List[str]
    skill_gaps: List[str]
    recommendations: List[SkillRecommendation]
    market_skills: Dict[str, Dict[str, Any]]
    jobs_analyzed: int
    analysis_date: str
    requires_setup: Optional[str] = None  # "skills" if user needs to add skills

    class Config:
        from_attributes = True


@router.get("/skills", response_model=SkillAnalysisResponse)
async def get_skill_insights(
    refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get skill analysis and career recommendations for current user

    - **refresh**: Set to true to recompute analysis (default: use cached)

    Returns:
    - User's current skills
    - Skill gaps (in-demand skills user doesn't have)
    - Prioritized recommendations with learning effort estimates
    - Market skill data (frequency, salary impact)
    - Analysis metadata
    """
    try:
        # Check if user has skills - return empty response with setup flag
        if not current_user.skills or len(current_user.skills) == 0:
            from datetime import datetime
            return SkillAnalysisResponse(
                user_skills=[],
                skill_gaps=[],
                recommendations=[],
                market_skills={},
                jobs_analyzed=0,
                analysis_date=datetime.utcnow().isoformat(),
                requires_setup="skills"
            )

        # Check if analysis exists and is fresh
        analysis = db.query(SkillAnalysis).filter(
            SkillAnalysis.user_id == current_user.id
        ).first()

        if not analysis or refresh:
            # Run new analysis
            logger.info(f"Running skill analysis for user {current_user.id}")
            analysis = run_skill_analysis_for_user(db, current_user)

        # Convert recommendations to Pydantic models
        recommendations = [
            SkillRecommendation(**rec) for rec in analysis.recommendations
        ]

        return SkillAnalysisResponse(
            user_skills=analysis.user_skills,
            skill_gaps=analysis.skill_gaps,
            recommendations=recommendations,
            market_skills=analysis.market_skills,
            jobs_analyzed=analysis.jobs_analyzed,
            analysis_date=analysis.analysis_date.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill insights for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get skill insights"
        )


@router.post("/skills/refresh", response_model=SkillAnalysisResponse)
@limiter.limit("5/hour")  # Expensive operation - analyzes all jobs
async def refresh_skill_insights(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Force refresh of skill analysis for current user

    This will:
    1. Analyze all jobs in database for skill trends
    2. Identify gaps in user's skill set
    3. Generate prioritized recommendations
    4. Update cached analysis
    """
    try:
        # Check if user has skills - return empty response with setup flag
        if not current_user.skills or len(current_user.skills) == 0:
            from datetime import datetime
            return SkillAnalysisResponse(
                user_skills=[],
                skill_gaps=[],
                recommendations=[],
                market_skills={},
                jobs_analyzed=0,
                analysis_date=datetime.utcnow().isoformat(),
                requires_setup="skills"
            )

        # Run new analysis
        logger.info(f"Refreshing skill analysis for user {current_user.id}")
        analysis = run_skill_analysis_for_user(db, current_user)

        # Convert recommendations to Pydantic models
        recommendations = [
            SkillRecommendation(**rec) for rec in analysis.recommendations
        ]

        return SkillAnalysisResponse(
            user_skills=analysis.user_skills,
            skill_gaps=analysis.skill_gaps,
            recommendations=recommendations,
            market_skills=analysis.market_skills,
            jobs_analyzed=analysis.jobs_analyzed,
            analysis_date=analysis.analysis_date.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing skill insights for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh skill insights"
        )
