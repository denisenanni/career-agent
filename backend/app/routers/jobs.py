from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("")
async def list_jobs(
    source: Optional[str] = None,
    job_type: Optional[str] = None,
    remote_type: Optional[str] = None,
    min_salary: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
):
    """List jobs with optional filters."""
    # TODO: Implement database query
    return {
        "jobs": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get job details by ID."""
    # TODO: Implement database query
    return {"error": "Not implemented"}


@router.post("/refresh")
async def refresh_jobs():
    """Trigger job scraping."""
    # TODO: Implement scraping trigger
    return {"status": "queued", "message": "Scraping job queued"}
