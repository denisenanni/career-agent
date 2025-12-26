from fastapi import APIRouter, Query, Depends, HTTPException, BackgroundTasks, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, over, text
from typing import Optional
from enum import Enum
import logging
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.job import Job
from app.models.scrape_log import ScrapeLog
from app.models.user import User
from app.schemas.job import JobsResponse, JobDetail, JobListItem, ScrapeLogResponse, PaginationInfo
from math import ceil
from app.dependencies.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


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
    authenticjobs = "authenticjobs"
    jobspy_indeed = "jobspy_indeed"
    jobspy_google = "jobspy_google"


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
    skills: Optional[str] = Query(None, max_length=500, description="Comma-separated skills to filter by"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List jobs with optional filters.

    - **source**: Filter by job source (remoteok, weworkremotely)
    - **job_type**: Filter by job type (permanent, contract, freelance, part-time)
    - **remote_type**: Filter by remote type (full, hybrid, onsite)
    - **min_salary**: Minimum salary filter
    - **search**: Search in title, company, and description
    - **skills**: Comma-separated list of skills to filter by (matches jobs with ANY of the skills)
    - **page**: Page number (starts at 1)
    - **per_page**: Number of results per page (max 100)
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
        # plainto_tsquery safely converts plain text to tsquery format
        query = query.filter(
            text("search_vector @@ plainto_tsquery('english', :search)")
        ).params(search=search)
    if skills:
        # Filter by skills (case-insensitive match in tags JSON array)
        skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
        if skill_list:
            # Use PostgreSQL JSON array containment with case-insensitive matching
            # Check if any of the provided skills match any tag in the job
            skill_conditions = " OR ".join([
                f"EXISTS (SELECT 1 FROM json_array_elements_text(tags::json) AS tag WHERE lower(tag) = :skill_{i})"
                for i in range(len(skill_list))
            ])
            params = {f"skill_{i}": skill for i, skill in enumerate(skill_list)}
            query = query.filter(
                text(f"tags IS NOT NULL AND ({skill_conditions})")
            ).params(**params)

    # Calculate offset from page
    offset = (page - 1) * per_page

    # Optimize: Use window function to get count in same query (single DB hit instead of two)
    # Add row count as a window function
    count_column = func.count().over().label('total_count')
    query_with_count = query.add_columns(count_column)

    # Get paginated results with count
    results = query_with_count.order_by(Job.scraped_at.desc()).offset(offset).limit(per_page).all()

    # Extract jobs and total count
    if results:
        jobs = [row[0] for row in results]  # First element is the Job object
        total = results[0][1]  # Second element is the total_count from window function
    else:
        jobs = []
        total = 0

    # Calculate pagination metadata
    total_pages = ceil(total / per_page) if total > 0 else 0

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
        pagination=PaginationInfo(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
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
    """Background task to run all scrapers."""
    all_stats = {}

    # RemoteOK
    try:
        logger.info("Starting RemoteOK scraper...")
        from app.scrapers.remoteok import scrape_and_save as remoteok_scrape
        stats = await remoteok_scrape()
        all_stats["remoteok"] = stats
        logger.info(f"RemoteOK completed: {stats}")
    except Exception as e:
        logger.error(f"RemoteOK scraper failed: {str(e)}", exc_info=True)
        all_stats["remoteok"] = {"error": str(e)}

    # We Work Remotely
    try:
        logger.info("Starting We Work Remotely scraper...")
        from app.scrapers.weworkremotely import scrape_and_save as wwr_scrape
        stats = await wwr_scrape()
        all_stats["weworkremotely"] = stats
        logger.info(f"We Work Remotely completed: {stats}")
    except Exception as e:
        logger.error(f"We Work Remotely scraper failed: {str(e)}", exc_info=True)
        all_stats["weworkremotely"] = {"error": str(e)}

    # HackerNews Who's Hiring
    try:
        logger.info("Starting HackerNews scraper...")
        from app.scrapers.hackernews import scrape_and_save as hn_scrape
        stats = await hn_scrape()
        all_stats["hackernews"] = stats
        logger.info(f"HackerNews completed: {stats}")
    except Exception as e:
        logger.error(f"HackerNews scraper failed: {str(e)}", exc_info=True)
        all_stats["hackernews"] = {"error": str(e)}

    # Jobicy
    try:
        logger.info("Starting Jobicy scraper...")
        from app.scrapers.jobicy import scrape_and_save as jobicy_scrape
        stats = await jobicy_scrape()
        all_stats["jobicy"] = stats
        logger.info(f"Jobicy completed: {stats}")
    except Exception as e:
        logger.error(f"Jobicy scraper failed: {str(e)}", exc_info=True)
        all_stats["jobicy"] = {"error": str(e)}

    # Authentic Jobs
    try:
        logger.info("Starting Authentic Jobs scraper...")
        from app.scrapers.authenticjobs import scrape_and_save as authenticjobs_scrape
        stats = await authenticjobs_scrape()
        all_stats["authenticjobs"] = stats
        logger.info(f"Authentic Jobs completed: {stats}")
    except Exception as e:
        logger.error(f"Authentic Jobs scraper failed: {str(e)}", exc_info=True)
        all_stats["authenticjobs"] = {"error": str(e)}

    # JobSpy (Indeed + Google)
    try:
        logger.info("Starting JobSpy scraper (Indeed + Google)...")
        from app.scrapers.jobspy_scraper import scrape_and_save as jobspy_scrape
        stats = await jobspy_scrape()
        all_stats["jobspy"] = stats
        logger.info(f"JobSpy completed: {stats}")
    except Exception as e:
        logger.error(f"JobSpy scraper failed: {str(e)}", exc_info=True)
        all_stats["jobspy"] = {"error": str(e)}

    logger.info(f"All scrapers completed: {all_stats}")
    return all_stats


def verify_api_key(x_api_key: str = Header(None)) -> bool:
    """Verify the API key for scheduled scraping jobs."""
    if not settings.scraper_api_key:
        raise HTTPException(
            status_code=500,
            detail="SCRAPER_API_KEY not configured on server"
        )
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header required"
        )
    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, settings.scraper_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


@router.post("/scrape")
async def scrape_jobs(
    api_key_valid: bool = Depends(verify_api_key),
):
    """
    Run all job scrapers (for scheduled/cron jobs).

    Requires X-API-Key header with valid SCRAPER_API_KEY.
    This endpoint runs synchronously and returns when complete.
    Matching is automatically triggered for new jobs.
    """
    logger.info("Scheduled job scraping started via API key")
    try:
        stats = await run_scraper()
        return {
            "status": "completed",
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Scheduled scraping failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@router.post("/refresh")
@limiter.limit("2/hour")  # Expensive operation - web scraping
async def refresh_jobs(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger job scraping in the background.

    Requires authentication. Only authenticated users can trigger job scraping.
    """
    try:
        logger.info(f"Job scraping triggered by user {current_user.id}")
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
