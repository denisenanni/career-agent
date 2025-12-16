from fastapi import APIRouter, Query, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from enum import Enum
import os
import sys
import logging

from app.database import get_db
from app.models.job import Job
from app.models.scrape_log import ScrapeLog
from app.schemas.job import JobsResponse, JobDetail, JobListItem, ScrapeLogResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class JobType(str, Enum):
    """Valid job types"""
    permanent = "permanent"
    contract = "contract"
    freelance = "freelance"
    part_time = "part-time"


class RemoteType(str, Enum):
    """Valid remote types"""
    full = "full"
    hybrid = "hybrid"
    onsite = "onsite"


class JobSource(str, Enum):
    """Valid job sources"""
    remoteok = "remoteok"
    weworkremotely = "weworkremotely"


def truncate_description(description: str, max_length: int = 500) -> str:
    """Truncate description to max_length characters"""
    if len(description) > max_length:
        return description[:max_length] + "..."
    return description


def escape_sql_wildcards(text: str) -> str:
    """Escape SQL LIKE wildcards in user input"""
    return text.replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=JobsResponse)
async def list_jobs(
    source: Optional[JobSource] = None,
    job_type: Optional[JobType] = None,
    remote_type: Optional[RemoteType] = None,
    min_salary: Optional[int] = Query(None, ge=0),
    search: Optional[str] = Query(None, max_length=200),
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List jobs with optional filters.

    - **source**: Filter by job source (remoteok, weworkremotely)
    - **job_type**: Filter by job type (permanent, contract, freelance, part-time)
    - **remote_type**: Filter by remote type (full, hybrid, onsite)
    - **min_salary**: Minimum salary filter
    - **search**: Search in title, company, and description
    - **limit**: Number of results per page (max 100)
    - **offset**: Pagination offset
    """
    query = db.query(Job)

    # Apply filters
    if source:
        query = query.filter(Job.source == source.value)
    if job_type:
        query = query.filter(Job.job_type == job_type.value)
    if remote_type:
        query = query.filter(Job.remote_type == remote_type.value)
    if min_salary:
        query = query.filter(Job.salary_min >= min_salary)
    if search:
        # Use PostgreSQL full-text search (much faster than ILIKE)
        # Convert search query to tsquery format (handles AND/OR/NOT)
        # Replace spaces with & for AND search
        ts_query = ' & '.join(search.split())
        query = query.filter(
            Job.search_vector.match(ts_query)
        )

    # Get total count
    total = query.count()

    # Get paginated results
    jobs = query.order_by(Job.scraped_at.desc()).offset(offset).limit(limit).all()

    # Convert to response models with truncated descriptions
    job_items = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "source": job.source,
            "source_id": job.source_id,
            "url": job.url,
            "title": job.title,
            "company": job.company,
            "description": truncate_description(job.description),
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "location": job.location,
            "remote_type": job.remote_type,
            "job_type": job.job_type,
            "tags": job.tags or [],
            "posted_at": job.posted_at,
            "scraped_at": job.scraped_at,
        }
        job_items.append(JobListItem(**job_dict))

    return JobsResponse(
        jobs=job_items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get job details by ID.

    Returns full job details including complete description and raw data.
    """
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobDetail.model_validate(job)


async def run_scraper():
    """Background task to run the scraper."""
    try:
        logger.info("Starting background scraper task")

        # Get the scraping directory path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(current_dir))
        scraping_dir = os.path.join(os.path.dirname(backend_dir), "scraping")

        # Add scraping directory to path
        if scraping_dir not in sys.path:
            sys.path.insert(0, scraping_dir)

        from scrapers.remoteok import scrape_and_save

        stats = await scrape_and_save()
        logger.info(f"Scraper completed: {stats}")

    except Exception as e:
        logger.error(f"Scraper failed: {str(e)}", exc_info=True)
        raise


@router.post("/refresh")
async def refresh_jobs(background_tasks: BackgroundTasks):
    """
    Trigger job scraping in the background.

    Note: In production, consider adding rate limiting or authentication.
    """
    try:
        background_tasks.add_task(run_scraper)
        return {
            "status": "queued",
            "message": "Job scraping started in background",
        }
    except Exception as e:
        logger.error(f"Failed to queue scraper: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start job scraping"
        )


@router.get("/logs/latest", response_model=ScrapeLogResponse)
async def get_latest_scrape_logs(
    limit: int = Query(default=10, le=50, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get latest scrape logs.

    - **limit**: Number of logs to return (max 50)
    """
    logs = (
        db.query(ScrapeLog)
        .order_by(ScrapeLog.started_at.desc())
        .limit(limit)
        .all()
    )

    return ScrapeLogResponse(logs=logs)
