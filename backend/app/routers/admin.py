"""
Admin router - administrative endpoints for managing the application
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from typing import List
import logging

from app.database import get_db
from app.models.user import User
from app.models.allowed_email import AllowedEmail
from app.dependencies.auth import get_current_user
from app.services.redis_cache import get_cache_stats, reset_cache_metrics

logger = logging.getLogger(__name__)
router = APIRouter()


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if current user is an admin.

    Returns the user if they have admin privileges, otherwise raises 403.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Pydantic schemas
class AddAllowedEmailRequest(BaseModel):
    email: EmailStr


class AllowedEmailResponse(BaseModel):
    id: int
    email: str
    added_by: int | None
    created_at: str

    class Config:
        from_attributes = True


class AllowedEmailsListResponse(BaseModel):
    allowed_emails: List[AllowedEmailResponse]
    total: int


@router.post("/allowlist", response_model=AllowedEmailResponse, status_code=status.HTTP_201_CREATED)
async def add_allowed_email(
    email_data: AddAllowedEmailRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Add an email to the registration allowlist (admin only)

    - **email**: Email address to add to allowlist

    Returns the created allowlist entry.
    """
    email_lower = email_data.email.lower()

    # Check if already exists
    existing = db.query(AllowedEmail).filter(
        AllowedEmail.email == email_lower
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email_data.email}' is already on the allowlist"
        )

    # Create new allowlist entry
    new_allowed_email = AllowedEmail(
        email=email_lower,
        added_by=admin_user.id
    )

    try:
        db.add(new_allowed_email)
        db.commit()
        db.refresh(new_allowed_email)
        logger.info(f"Admin {admin_user.email} added {email_lower} to allowlist")
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email_data.email}' is already on the allowlist"
        )

    return AllowedEmailResponse(
        id=new_allowed_email.id,
        email=new_allowed_email.email,
        added_by=new_allowed_email.added_by,
        created_at=new_allowed_email.created_at.isoformat()
    )


@router.get("/allowlist", response_model=AllowedEmailsListResponse)
async def list_allowed_emails(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    List all emails on the registration allowlist (admin only)

    Returns list of all allowed emails.
    """
    allowed_emails = db.query(AllowedEmail).order_by(AllowedEmail.created_at.desc()).all()

    return AllowedEmailsListResponse(
        allowed_emails=[
            AllowedEmailResponse(
                id=ae.id,
                email=ae.email,
                added_by=ae.added_by,
                created_at=ae.created_at.isoformat()
            )
            for ae in allowed_emails
        ],
        total=len(allowed_emails)
    )


@router.delete("/allowlist/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_allowed_email(
    email: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Remove an email from the registration allowlist (admin only)

    - **email**: Email address to remove from allowlist

    Returns 204 No Content on success.
    """
    email_lower = email.lower()

    # Find the allowlist entry
    allowed_email = db.query(AllowedEmail).filter(
        AllowedEmail.email == email_lower
    ).first()

    if not allowed_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email '{email}' not found on allowlist"
        )

    db.delete(allowed_email)
    db.commit()
    logger.info(f"Admin {admin_user.email} removed {email_lower} from allowlist")

    return None


# =============================================================================
# Cache Monitoring Endpoints
# =============================================================================

@router.get("/cache/stats")
async def get_cache_statistics(
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Get Redis cache statistics and cost savings (admin only)

    Returns:
    - Overall hit/miss rates
    - Breakdown by cache type (cover letters, CV highlights, etc.)
    - Estimated cost savings from cache hits
    - Storage metrics (memory usage, key counts)
    """
    stats = get_cache_stats()

    if not stats.get("available", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=stats.get("error", "Redis not available")
        )

    return stats


@router.post("/cache/reset-metrics", status_code=status.HTTP_200_OK)
async def reset_cache_statistics(
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Reset cache metrics counters (admin only)

    This resets hit/miss counters but does NOT clear cached data.
    Useful for starting fresh metrics tracking.
    """
    success = reset_cache_metrics()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to reset metrics - Redis not available"
        )

    logger.info(f"Admin {admin_user.email} reset cache metrics")
    return {"message": "Cache metrics reset successfully"}
