"""
User Jobs router - user-submitted job postings
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import json
from datetime import datetime
import uuid
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.models.user_job import UserJob
from app.models.job import Job
from app.dependencies.auth import get_current_user
from app.services.llm import client as llm_client
from app.services.matching import create_match_for_job
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


# Pydantic schemas
class ParseJobRequest(BaseModel):
    job_text: str = Field(..., min_length=50, description="Pasted job posting text")


class UserJobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    description: str = Field(..., min_length=1)
    url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    remote_type: Optional[str] = None  # full, hybrid, onsite
    job_type: Optional[str] = None  # permanent, contract, part-time
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = "USD"
    tags: Optional[List[str]] = Field(default_factory=list)


class UserJobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    remote_type: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    tags: Optional[List[str]] = None


class UserJobResponse(BaseModel):
    id: int
    user_id: int
    title: str
    company: Optional[str]
    description: str
    url: Optional[str]
    source: str
    tags: List[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: str
    location: Optional[str]
    remote_type: Optional[str]
    job_type: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UserJobsListResponse(BaseModel):
    jobs: List[UserJobResponse]
    total: int


def parse_job_with_llm(job_text: str) -> dict:
    """
    Parse pasted job text using Claude Haiku to extract structured information.

    Args:
        job_text: Raw job posting text pasted by user

    Returns:
        Dictionary with extracted job fields

    Raises:
        ValueError: If parsing fails or returns invalid data
    """
    prompt = f"""Extract job information from this pasted job posting. Return ONLY valid JSON, no markdown, no explanations.

Extract these fields:
- title: Job title (required)
- company: Company name or null
- description: Clean job description text
- url: Job posting URL if present in the text, or null
- location: Location string or null
- remote_type: "full", "hybrid", "onsite", or null
- job_type: "permanent", "contract", "part-time", or null
- salary_min: Minimum salary number or null
- salary_max: Maximum salary number or null
- salary_currency: "USD", "EUR", "GBP", etc. (default USD)
- required_skills: Array of skill strings
- nice_to_have_skills: Array of skill strings
- experience_years_min: Number or null

Pasted Job Text:
---
{job_text}
---

Return JSON only:"""

    if not llm_client:
        raise ValueError("AI parsing is not available (API key not configured)")

    try:
        response = llm_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # Parse JSON
        parsed = json.loads(content)

        # Validate required fields
        if not parsed.get("title"):
            raise ValueError("Missing required field: title")

        # Combine skills into tags
        tags = []
        if parsed.get("required_skills"):
            tags.extend(parsed["required_skills"])
        if parsed.get("nice_to_have_skills"):
            tags.extend(parsed["nice_to_have_skills"])

        # Remove duplicates from tags
        tags = list(set(tags))

        return {
            "title": parsed["title"],
            "company": parsed.get("company"),
            "description": parsed.get("description", job_text),
            "url": parsed.get("url"),
            "location": parsed.get("location"),
            "remote_type": parsed.get("remote_type"),
            "job_type": parsed.get("job_type"),
            "salary_min": parsed.get("salary_min"),
            "salary_max": parsed.get("salary_max"),
            "salary_currency": parsed.get("salary_currency", "USD"),
            "tags": tags,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"LLM response: {content}")
        raise ValueError(f"Failed to parse job text: Invalid JSON response from AI")
    except Exception as e:
        logger.error(f"Error parsing job with LLM: {e}", exc_info=True)
        raise ValueError("Failed to parse job text. Please try again.")


@router.post("/parse", response_model=UserJobCreate)
@limiter.limit("10/hour")
async def parse_job_text(
    request: ParseJobRequest,
    http_request: Request,  # Required for rate limiter
    current_user: User = Depends(get_current_user)
):
    """
    Parse pasted job text using AI and return extracted structured data.

    The user can review and edit before saving.

    - **job_text**: Raw job posting text (minimum 50 characters)

    Returns extracted job information ready to be saved.

    Rate limited to 10 requests per hour per user.
    """
    try:
        parsed_data = parse_job_with_llm(request.job_text)
        return UserJobCreate(**parsed_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse job text"
        )


@router.post("", response_model=UserJobResponse, status_code=status.HTTP_201_CREATED)
async def create_user_job(
    job_data: UserJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user-submitted job posting and automatically create a match.

    - **title**: Job title (required)
    - **company**: Company name (optional)
    - **description**: Job description (required)
    - **url**: Job posting URL (optional)
    - Additional fields: location, remote_type, job_type, salary, tags

    Returns the created job with generated ID.

    Note: Also creates a corresponding Job entry for matching purposes.
    """
    # Create the main Job entry (for matching system)
    # Use UUID to ensure unique source_id
    unique_id = str(uuid.uuid4())[:8]
    job_entry = Job(
        source="user_submitted",
        source_id=f"user_{current_user.id}_{unique_id}",
        url=job_data.url or "",
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
        salary_currency=job_data.salary_currency or "USD",
        location=job_data.location,
        remote_type=job_data.remote_type,
        job_type=job_data.job_type,
        tags=job_data.tags or [],
        raw_data={"user_submitted": True, "user_id": current_user.id},
    )

    # Create new user job
    new_job = UserJob(
        user_id=current_user.id,
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
        url=job_data.url,
        location=job_data.location,
        remote_type=job_data.remote_type,
        job_type=job_data.job_type,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
        salary_currency=job_data.salary_currency or "USD",
        tags=job_data.tags or [],
    )

    try:
        # Add both to database
        db.add(job_entry)
        db.flush()  # Get job_entry.id before committing

        # Link UserJob to Job entry
        new_job.job_entry_id = job_entry.id

        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        db.refresh(job_entry)
        logger.info(f"User {current_user.id} created job {new_job.id}: {new_job.title}")

        # Create match for this job (async, in background)
        try:
            match = await create_match_for_job(db, current_user, job_entry, min_score=0)
            if match:
                logger.info(f"Created match {match.id} for user job {new_job.id} with score {match.score}")
            else:
                logger.info(f"No match created for user job {new_job.id} (score below threshold or no CV)")
        except Exception as e:
            # Don't fail the whole request if matching fails
            logger.error(f"Failed to create match for user job {new_job.id}: {e}")

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a job with this title and company"
        )

    return UserJobResponse(
        id=new_job.id,
        user_id=new_job.user_id,
        title=new_job.title,
        company=new_job.company,
        description=new_job.description,
        url=new_job.url,
        source=new_job.source,
        tags=new_job.tags or [],
        salary_min=new_job.salary_min,
        salary_max=new_job.salary_max,
        salary_currency=new_job.salary_currency,
        location=new_job.location,
        remote_type=new_job.remote_type,
        job_type=new_job.job_type,
        created_at=new_job.created_at.isoformat(),
        updated_at=new_job.updated_at.isoformat()
    )


@router.get("", response_model=UserJobsListResponse)
async def list_user_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all jobs submitted by the current user.

    Returns jobs ordered by creation date (newest first).
    """
    jobs = db.query(UserJob).filter(
        UserJob.user_id == current_user.id
    ).order_by(UserJob.created_at.desc()).all()

    return UserJobsListResponse(
        jobs=[
            UserJobResponse(
                id=job.id,
                user_id=job.user_id,
                title=job.title,
                company=job.company,
                description=job.description,
                url=job.url,
                source=job.source,
                tags=job.tags or [],
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                salary_currency=job.salary_currency,
                location=job.location,
                remote_type=job.remote_type,
                job_type=job.job_type,
                created_at=job.created_at.isoformat(),
                updated_at=job.updated_at.isoformat()
            )
            for job in jobs
        ],
        total=len(jobs)
    )


@router.get("/{job_id}", response_model=UserJobResponse)
async def get_user_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific user-submitted job.

    - **job_id**: ID of the job to retrieve

    Returns 404 if job not found or doesn't belong to current user.
    """
    job = db.query(UserJob).filter(
        UserJob.id == job_id,
        UserJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return UserJobResponse(
        id=job.id,
        user_id=job.user_id,
        title=job.title,
        company=job.company,
        description=job.description,
        url=job.url,
        source=job.source,
        tags=job.tags or [],
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        location=job.location,
        remote_type=job.remote_type,
        job_type=job.job_type,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat()
    )


@router.put("/{job_id}", response_model=UserJobResponse)
async def update_user_job(
    job_id: int,
    job_update: UserJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user-submitted job.

    - **job_id**: ID of the job to update
    - Provide only the fields you want to update

    Returns 404 if job not found or doesn't belong to current user.
    """
    job = db.query(UserJob).filter(
        UserJob.id == job_id,
        UserJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Update fields if provided
    update_data = job_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    try:
        db.commit()
        db.refresh(job)
        logger.info(f"User {current_user.id} updated job {job.id}")
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job with this title and company already exists"
        )

    return UserJobResponse(
        id=job.id,
        user_id=job.user_id,
        title=job.title,
        company=job.company,
        description=job.description,
        url=job.url,
        source=job.source,
        tags=job.tags or [],
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        location=job.location,
        remote_type=job.remote_type,
        job_type=job.job_type,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat()
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user-submitted job.

    - **job_id**: ID of the job to delete

    Returns 204 No Content on success.
    Returns 404 if job not found or doesn't belong to current user.

    Note: Also deletes the corresponding Job entry and any associated matches.
    """
    from app.models.match import Match

    user_job = db.query(UserJob).filter(
        UserJob.id == job_id,
        UserJob.user_id == current_user.id
    ).first()

    if not user_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Delete associated matches and Job entry if exists
    if user_job.job_entry_id:
        # Delete matches first (due to foreign key constraint)
        db.query(Match).filter(Match.job_id == user_job.job_entry_id).delete()

        # Delete the Job entry
        db.query(Job).filter(Job.id == user_job.job_entry_id).delete()

    # Delete the UserJob
    db.delete(user_job)
    db.commit()
    logger.info(f"User {current_user.id} deleted job {job_id} and associated entries")

    return None
