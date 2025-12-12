from fastapi import APIRouter
from typing import Optional

router = APIRouter()


@router.get("")
async def list_matches(
    min_score: Optional[float] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List job matches for user."""
    # TODO: Implement
    return {
        "matches": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{job_id}/generate")
async def generate_application(job_id: str):
    """Generate cover letter and CV highlights for a job."""
    # TODO: Implement LLM generation
    return {
        "job_id": job_id,
        "cover_letter": None,
        "cv_highlights": None,
        "status": "not_implemented",
    }


@router.put("/{job_id}/status")
async def update_match_status(job_id: str, status: str):
    """Update match status (interested, applied, rejected, hidden)."""
    # TODO: Implement
    return {"job_id": job_id, "status": status}
