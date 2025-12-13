"""Job-related Pydantic schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class JobBase(BaseModel):
    """Base job schema with common fields"""
    id: int
    source: str
    source_id: str
    url: str
    title: str
    company: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str
    location: str
    remote_type: str
    job_type: str
    tags: List[str] = Field(default_factory=list)
    posted_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListItem(JobBase):
    """Job schema for list view (with truncated description)"""
    description: str


class JobDetail(JobBase):
    """Job schema for detail view (with full description and raw_data)"""
    description: str
    raw_data: Optional[dict] = None


class JobsResponse(BaseModel):
    """Response schema for jobs list endpoint"""
    jobs: List[JobListItem]
    total: int
    limit: int
    offset: int


class ScrapeLogItem(BaseModel):
    """Scrape log item schema"""
    id: int
    source: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    jobs_found: int
    jobs_new: int
    status: str
    error: Optional[str] = None

    class Config:
        from_attributes = True


class ScrapeLogResponse(BaseModel):
    """Response schema for scrape logs endpoint"""
    logs: List[ScrapeLogItem]
