"""
Matches router - job matching and application generation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import User, Match, Job
from app.dependencies.auth import get_current_user
from app.services.matching import match_user_with_all_jobs
from app.services.generation import generate_cover_letter, generate_cv_highlights
from app.services.redis_cache import cache_delete_pattern, build_match_content_pattern
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


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


class CoverLetterResponse(BaseModel):
    cover_letter: str
    cached: bool
    generated_at: str


class CVHighlightsResponse(BaseModel):
    highlights: List[str]
    cached: bool
    generated_at: str


class RegenerateResponse(BaseModel):
    message: str
    keys_invalidated: int


@router.get("", response_model=MatchListResponse)
async def list_matches(
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    max_score: Optional[float] = Query(default=None, ge=0, le=100),
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List job matches for current user

    - **min_score**: Filter by minimum match score (0-100)
    - **max_score**: Filter by maximum match score (0-100)
    - **status**: Filter by status (matched, interested, applied, rejected, hidden)
    - **limit**: Number of results per page (default 50, max 100)
    - **offset**: Pagination offset
    """

    # Build query with eager loading to avoid N+1 queries
    query = db.query(Match).options(joinedload(Match.job)).filter(Match.user_id == current_user.id)

    # Apply filters
    if min_score is not None:
        query = query.filter(Match.score >= min_score)

    if max_score is not None:
        query = query.filter(Match.score <= max_score)

    if status:
        # If specific status requested, show only that status
        query = query.filter(Match.status == status)
    else:
        # By default, exclude hidden and rejected matches
        query = query.filter(~Match.status.in_(["hidden", "rejected"]))

    # Get total count (without eager loading for efficiency)
    count_query = db.query(Match).filter(Match.user_id == current_user.id)
    if min_score is not None:
        count_query = count_query.filter(Match.score >= min_score)
    if max_score is not None:
        count_query = count_query.filter(Match.score <= max_score)
    if status:
        count_query = count_query.filter(Match.status == status)
    else:
        count_query = count_query.filter(~Match.status.in_(["hidden", "rejected"]))
    total = count_query.count()

    # Get paginated results, ordered by score
    matches = query.order_by(Match.score.desc()).limit(limit).offset(offset).all()

    # Build response using eagerly loaded job relationship
    match_responses = []
    for match in matches:
        if match.job:
            match_responses.append(MatchResponse(
                id=match.id,
                job_id=match.job_id,
                score=match.score,
                status=match.status,
                reasoning=match.reasoning or {},
                analysis=match.analysis or "",
                created_at=match.created_at.isoformat(),
                job_title=match.job.title,
                job_company=match.job.company,
                job_url=match.job.url,
                job_location=match.job.location or "Remote",
                job_remote_type=match.job.remote_type or "full",
                job_salary_min=match.job.salary_min,
                job_salary_max=match.job.salary_max,
            ))

    return MatchListResponse(
        matches=match_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/refresh", response_model=RefreshMatchesResponse)
@limiter.limit("5/hour")  # Expensive operation - LLM calls for all jobs
async def refresh_matches(
    request: Request,
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
        from datetime import datetime, timezone
        match.applied_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(match)

    return {"match_id": match_id, "status": match.status}


@router.post("/{match_id}/generate-cover-letter", response_model=CoverLetterResponse)
@limiter.limit("20/hour")  # LLM call (Sonnet) - cached after first generation
async def generate_match_cover_letter(
    request: Request,
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a personalized cover letter for a match

    This endpoint will:
    1. Check Redis cache first for existing cover letter
    2. If cached, return instantly (sub-50ms response)
    3. If not cached, generate using Claude Sonnet and cache for 30 days
    """
    # Find match and verify ownership
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

    # Generate cover letter
    result = generate_cover_letter(current_user, job, match)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cover letter"
        )

    return CoverLetterResponse(**result)


@router.post("/{match_id}/generate-highlights", response_model=CVHighlightsResponse)
@limiter.limit("20/hour")  # LLM call (Haiku) - cached after first generation
async def generate_match_highlights(
    request: Request,
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate tailored CV highlights for a match

    This endpoint will:
    1. Check Redis cache first for existing highlights
    2. If cached, return instantly (sub-50ms response)
    3. If not cached, generate using Claude Haiku and cache for 30 days
    """
    # Find match and verify ownership
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

    # Generate CV highlights
    result = generate_cv_highlights(current_user, job, match)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate CV highlights"
        )

    return CVHighlightsResponse(**result)


@router.post("/{match_id}/regenerate", response_model=RegenerateResponse)
async def regenerate_match_content(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clear cache and force regeneration of all content for a match

    This is useful when:
    - User has updated their CV or profile
    - User wants fresh content with different wording
    - Cached content is outdated

    This will invalidate the cache for both cover letter and CV highlights.
    The next request will generate fresh content.
    """
    # Find match and verify ownership
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Get job details to get job_id
    job = db.query(Job).filter(Job.id == match.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated job not found"
        )

    # Invalidate all cached content for this match
    pattern = build_match_content_pattern(current_user.id, job.id)
    keys_invalidated = cache_delete_pattern(pattern)

    logger.info(f"Invalidated {keys_invalidated} cache keys for match {match_id}")

    return RegenerateResponse(
        message=f"Cache cleared for match {match_id}. Next generation will create fresh content.",
        keys_invalidated=keys_invalidated
    )
