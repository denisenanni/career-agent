"""
Matches router - job matching and application generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models import User, Match, Job
from app.dependencies.auth import get_current_user
from app.services.matching import match_user_with_all_jobs

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class MatchResponse(BaseModel):
    id: int
    job_id: int
    score: float
    status: str
    reasoning: dict
    analysis: str
    created_at: str

    # Include job details
    job_title: str
    job_company: str
    job_url: str
    job_location: str
    job_remote_type: str
    job_salary_min: Optional[int]
    job_salary_max: Optional[int]

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
    total: int
    limit: int
    offset: int


class MatchStatusUpdate(BaseModel):
    status: str  # interested, applied, rejected, hidden


class RefreshMatchesResponse(BaseModel):
    matches_created: int
    matches_updated: int
    total_jobs_processed: int


@router.get("", response_model=MatchListResponse)
async def list_matches(
    min_score: Optional[float] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List job matches for current user

    - **min_score**: Filter by minimum match score (0-100)
    - **status**: Filter by status (matched, interested, applied, rejected, hidden)
    - **limit**: Number of results per page (default 50, max 100)
    - **offset**: Pagination offset
    """
    # Validate limit
    if limit > 100:
        limit = 100

    # Build query
    query = db.query(Match).filter(Match.user_id == current_user.id)

    # Apply filters
    if min_score is not None:
        query = query.filter(Match.score >= min_score)

    if status:
        query = query.filter(Match.status == status)

    # Get total count
    total = query.count()

    # Get paginated results, ordered by score
    matches = query.order_by(Match.score.desc()).limit(limit).offset(offset).all()

    # Enrich with job details
    match_responses = []
    for match in matches:
        job = db.query(Job).filter(Job.id == match.job_id).first()
        if job:
            match_responses.append(MatchResponse(
                id=match.id,
                job_id=match.job_id,
                score=match.score,
                status=match.status,
                reasoning=match.reasoning or {},
                analysis=match.analysis or "",
                created_at=match.created_at.isoformat(),
                job_title=job.title,
                job_company=job.company,
                job_url=job.url,
                job_location=job.location or "Remote",
                job_remote_type=job.remote_type or "full",
                job_salary_min=job.salary_min,
                job_salary_max=job.salary_max,
            ))

    return MatchListResponse(
        matches=match_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/refresh", response_model=RefreshMatchesResponse)
async def refresh_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Refresh matches for current user against all jobs

    This will:
    1. Match user profile against all jobs in database
    2. Create new matches for qualifying jobs (score >= 60)
    3. Update existing matches with new scores
    """
    try:
        # Get count before
        matches_before = db.query(Match).filter(Match.user_id == current_user.id).count()

        # Run matching
        matches = await match_user_with_all_jobs(db, current_user, min_score=60.0)

        # Get count after
        matches_after = db.query(Match).filter(Match.user_id == current_user.id).count()

        # Calculate stats
        matches_created = matches_after - matches_before
        matches_updated = len(matches) - matches_created

        # Get total jobs processed
        total_jobs = db.query(func.count(Job.id)).scalar()

        return RefreshMatchesResponse(
            matches_created=matches_created,
            matches_updated=matches_updated,
            total_jobs_processed=total_jobs,
        )
    except Exception as e:
        logger.error(f"Error refreshing matches for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh matches"
        )


@router.get("/{match_id}")
async def get_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific match"""
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Get job details
    job = db.query(Job).filter(Job.id == match.job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated job not found"
        )

    return {
        "match": match,
        "job": job,
    }


@router.put("/{match_id}/status")
async def update_match_status(
    match_id: int,
    status_update: MatchStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update match status

    - **interested**: User is interested in this job
    - **applied**: User has applied to this job
    - **rejected**: User rejected this job
    - **hidden**: User wants to hide this match
    """
    # Validate status
    valid_statuses = ["matched", "interested", "applied", "rejected", "hidden"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    # Find match
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Update status
    match.status = status_update.status

    # Set applied_at if status is applied
    if status_update.status == "applied":
        from datetime import datetime
        match.applied_at = datetime.utcnow()

    db.commit()
    db.refresh(match)

    return {"match_id": match_id, "status": match.status}


@router.post("/{job_id}/generate")
async def generate_application(job_id: int):
    """
    Generate cover letter and CV highlights for a job

    NOTE: This will be implemented in Phase 5
    """
    # TODO: Implement LLM generation in Phase 5
    return {
        "job_id": job_id,
        "cover_letter": None,
        "cv_highlights": None,
        "status": "not_implemented",
    }
