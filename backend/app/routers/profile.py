"""
Profile router - user profile management and CV upload
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.profile import ProfileUpdate, CVUploadResponse, ProfileResponse
from app.utils.cv_parser import extract_cv_text, validate_cv_file

router = APIRouter()


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
    # Update fields that were provided
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    # Update timestamp
    current_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/cv", response_model=CVUploadResponse)
async def upload_cv(
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

        # Update user profile with CV data
        current_user.cv_text = cv_text
        current_user.cv_filename = file.filename
        current_user.cv_uploaded_at = datetime.now(timezone.utc)
        current_user.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(current_user)

        return CVUploadResponse(
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            cv_text_length=len(cv_text),
            uploaded_at=current_user.cv_uploaded_at,
            message=f"CV uploaded successfully. Extracted {len(cv_text)} characters of text."
        )

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
