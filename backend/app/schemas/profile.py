"""
Profile-related schemas for CV upload and user profile management
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProfileUpdate(BaseModel):
    """Profile update request"""
    full_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=1000)
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=70)
    preferences: Optional[dict] = None


class CVUploadResponse(BaseModel):
    """CV upload response"""
    filename: str
    file_size: int
    content_type: str
    cv_text_length: int
    uploaded_at: datetime
    message: str


class ParsedCVUpdate(BaseModel):
    """Update parsed CV data"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    years_of_experience: Optional[int] = Field(None, ge=0, le=70)


class ProfileResponse(BaseModel):
    """User profile response"""
    id: int
    email: str
    full_name: Optional[str]
    bio: Optional[str]
    skills: List[str]
    experience_years: Optional[int]
    preferences: Optional[dict] = None
    cv_filename: Optional[str]
    cv_uploaded_at: Optional[datetime]
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
