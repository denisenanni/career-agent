from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from datetime import datetime
from app.models import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Auth
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Profile
    full_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    skills = Column(JSON, default=list)  # List of skills
    experience_years = Column(Integer, nullable=True)

    # Preferences
    preferences = Column(JSON, default=dict)  # Job preferences, filters, etc.

    # CV
    cv_text = Column(Text, nullable=True)  # Extracted CV text
    cv_filename = Column(String, nullable=True)
    cv_uploaded_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
