"""
Profile router - user profile management and CV upload
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user, invalidate_user_cache
from app.schemas.profile import ProfileUpdate, CVUploadResponse, ProfileResponse, ParsedCVUpdate
from app.utils.cv_parser import extract_cv_text, validate_cv_file
from app.services.llm import parse_cv_with_llm
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's profile

    Returns complete profile information including CV upload status.
    Requires authentication.
    """
    return current_user


@router.put("", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user profile

    - **full_name**: User's full name
    - **bio**: Short biography (max 1000 chars)
    - **skills**: List of skills
    - **experience_years**: Years of professional experience (0-70)
    - **preferences**: Job preferences as JSON object
    """
    # Query user from database to ensure it's attached to the session
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields that were provided
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        # Special handling for preferences: merge instead of overwrite
        if field == 'preferences' and value is not None:
            # Preserve existing preferences and merge with new ones
            existing_prefs = user.preferences or {}
            merged_prefs = {**existing_prefs, **value}
            setattr(user, field, merged_prefs)
        else:
            setattr(user, field, value)

    # Update timestamp
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Invalidate user cache to ensure fresh data on next request
    invalidate_user_cache(user.id)

    return user


@router.post("/cv", response_model=CVUploadResponse)
@limiter.limit("5/hour")  # Limit to 5 CV uploads per hour per IP
async def upload_cv(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload and parse CV file

    Supports:
    - **PDF** (.pdf)
    - **Word** (.docx)
    - **Text** (.txt)

    Maximum file size: 5MB

    The CV text will be extracted and stored for job matching.
    """
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Query user from database to ensure it's attached to the session
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:
        # Validate file
        validate_cv_file(file.filename, file_size, max_size_mb=5)

        # Extract text from CV
        cv_text = extract_cv_text(file.filename, file_content)

        if not cv_text or len(cv_text.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV text is too short or empty. Please upload a valid CV with more content."
            )

        # Parse CV with Claude Haiku
        parsed_data = parse_cv_with_llm(cv_text)

        # Update user profile with CV data
        user.cv_text = cv_text
        user.cv_filename = file.filename
        user.cv_uploaded_at = datetime.now(timezone.utc)
        user.updated_at = datetime.utcnow()

        # If LLM parsing succeeded, update profile with parsed data
        if parsed_data:
            logger.info(f"Successfully parsed CV for user {user.id}: {parsed_data.get('name')}")

            # Update name if provided and not already set
            if parsed_data.get('name') and not user.full_name:
                user.full_name = parsed_data['name']

            # Update skills if provided
            if parsed_data.get('skills'):
                # Merge with existing skills if any
                existing_skills = user.skills or []
                new_skills = parsed_data['skills']
                # Combine and deduplicate
                user.skills = list(set(existing_skills + new_skills))

            # Update experience years if provided and not already set
            if parsed_data.get('years_of_experience') and not user.experience_years:
                user.experience_years = parsed_data['years_of_experience']

            # Store full parsed data in preferences for now (we can use it later)
            # Important: Create a new dict to trigger SQLAlchemy's change detection
            preferences = user.preferences.copy() if user.preferences else {}
            preferences['parsed_cv'] = parsed_data
            user.preferences = preferences
        else:
            logger.warning(f"LLM parsing failed for user {user.id}, CV text still saved")

        db.commit()
        db.refresh(user)

        # Invalidate user cache to ensure fresh data on next request
        invalidate_user_cache(user.id)

        return CVUploadResponse(
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            cv_text_length=len(cv_text),
            uploaded_at=user.cv_uploaded_at,
            message=f"CV uploaded successfully. Extracted {len(cv_text)} characters of text." +
                    (f" Parsed with Claude Haiku: {parsed_data.get('name', 'Unknown')}" if parsed_data else " (LLM parsing unavailable)")
        )

    except HTTPException:
        # Re-raise HTTPException as-is (from short content check, etc.)
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CV: {str(e)}"
        )


@router.get("/cv/parsed")
async def get_parsed_cv(
    current_user: User = Depends(get_current_user),
):
    """
    Get parsed CV data extracted by Claude Haiku

    Returns structured data including:
    - Name, email, phone
    - Professional summary
    - Skills list
    - Work experience
    - Education
    - Years of experience

    Returns None if CV hasn't been uploaded or parsed yet.
    """
    if not current_user.preferences or 'parsed_cv' not in current_user.preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No parsed CV data found. Please upload a CV first."
        )

    return current_user.preferences['parsed_cv']


@router.put("/cv/parsed")
async def update_parsed_cv(
    cv_data: ParsedCVUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update parsed CV data

    Allows editing of parsed CV fields:
    - **name**: Full name
    - **email**: Email address
    - **phone**: Phone number
    - **summary**: Professional summary
    - **skills**: List of skills
    - **experience**: Work experience array
    - **education**: Education array
    - **years_of_experience**: Total years of experience

    This updates the parsed_cv data in preferences and also syncs
    relevant fields to the main profile (name, skills, experience_years).
    """
    # Query user from database to ensure it's attached to the session
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.preferences or 'parsed_cv' not in user.preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No parsed CV data found. Please upload a CV first."
        )

    # Get current parsed CV
    parsed_cv = user.preferences['parsed_cv'].copy()

    # Update only provided fields
    update_data = cv_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        parsed_cv[field] = value

    # Update preferences with new parsed_cv
    preferences = user.preferences.copy()
    preferences['parsed_cv'] = parsed_cv
    user.preferences = preferences

    # Sync key fields to main profile
    if 'name' in update_data:
        user.full_name = update_data['name']

    if 'skills' in update_data:
        user.skills = update_data['skills']

    if 'years_of_experience' in update_data:
        user.experience_years = update_data['years_of_experience']

    # Update timestamp
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Invalidate user cache to ensure fresh data on next request
    invalidate_user_cache(user.id)

    return parsed_cv
