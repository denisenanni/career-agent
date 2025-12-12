from fastapi import APIRouter, UploadFile, File
from typing import Optional

router = APIRouter()


@router.get("")
async def get_profile():
    """Get user profile."""
    # TODO: Implement with auth
    return {"error": "Not implemented"}


@router.put("")
async def update_profile(
    skills: Optional[list[str]] = None,
    experience_years: Optional[int] = None,
    preferences: Optional[dict] = None,
):
    """Update user profile."""
    # TODO: Implement
    return {"error": "Not implemented"}


@router.post("/cv")
async def upload_cv(file: UploadFile = File(...)):
    """Upload and parse CV."""
    # TODO: Implement CV parsing
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "uploaded",
        "message": "CV parsing not yet implemented",
    }
