from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.models import Base


class AllowedEmail(Base):
    __tablename__ = "allowed_emails"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    added_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AllowedEmail(id={self.id}, email='{self.email}')>"
