"""Job-related Pydantic schemas"""
from pydantic import BaseModel, Field, field_validator, HttpUrl
from datetime import datetime
from typing import Optional, List, Any, Dict
import html
import re


# Constants for validation
MAX_TITLE_LENGTH = 500
MAX_COMPANY_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 50000
MAX_URL_LENGTH = 2000
MAX_LOCATION_LENGTH = 200
MAX_SOURCE_ID_LENGTH = 200
MAX_TAG_LENGTH = 100
MAX_TAGS_COUNT = 50

# Compiled regex patterns (compile once, use many times for performance)
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


def sanitize_html_content(value: Any, max_depth: int = 3, current_depth: int = 0) -> Any:
    """
    Sanitize HTML content to prevent XSS attacks.
    Escapes HTML entities in strings and recursively processes dicts/lists.

    Args:
        value: The value to sanitize
        max_depth: Maximum recursion depth (default: 3, prevents deep object traversal)
        current_depth: Current recursion level (internal use)

    Returns:
        Sanitized value with HTML entities escaped
    """
    if value is None:
        return None

    # Prevent excessive recursion for performance
    if current_depth >= max_depth:
        return value

    if isinstance(value, str):
        # Only escape if string contains potential HTML
        if '<' in value or '>' in value or '&' in value:
            return html.escape(value)
        return value

    if isinstance(value, dict):
        # Selective sanitization: only sanitize values likely to contain user content
        # Skip technical fields that won't be displayed as HTML
        skip_keys = {'id', 'timestamp', 'date', 'created', 'updated', 'count', 'index'}
        return {
            k: sanitize_html_content(v, max_depth, current_depth + 1)
            if not any(skip in k.lower() for skip in skip_keys)
            else v
            for k, v in value.items()
        }

    if isinstance(value, list):
        # Only process first few items for large lists to avoid performance hit
        if len(value) > 100:
            # For large lists, only sanitize first 100 items
            return [
                sanitize_html_content(item, max_depth, current_depth + 1)
                for item in value[:100]
            ] + value[100:]
        return [sanitize_html_content(item, max_depth, current_depth + 1) for item in value]

    return value


class JobScrapedData(BaseModel):
    """
    Validation schema for scraped job data before saving to database.
    Ensures all required fields are present and validates data format/length.
    """
    source_id: str = Field(..., min_length=1, max_length=MAX_SOURCE_ID_LENGTH)
    url: str = Field(..., min_length=1, max_length=MAX_URL_LENGTH)
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    company: str = Field(..., min_length=1, max_length=MAX_COMPANY_LENGTH)
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH)

    # Optional fields with defaults
    salary_min: Optional[int] = Field(None, ge=0, le=10000000)
    salary_max: Optional[int] = Field(None, ge=0, le=10000000)
    salary_currency: Optional[str] = Field(default=None, max_length=10)
    location: str = Field(default="Remote", max_length=MAX_LOCATION_LENGTH)
    remote_type: str = Field(default="full", max_length=20)
    job_type: str = Field(default="permanent", max_length=20)
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS_COUNT)
    posted_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format using pre-compiled regex for performance"""
        if not URL_PATTERN.match(v):
            raise ValueError(f'Invalid URL format: {v}')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags list - ensure no empty strings and enforce max length per tag"""
        if not v:
            return []

        # Remove empty strings and validate length
        validated_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                tag_clean = tag.strip()
                if len(tag_clean) > MAX_TAG_LENGTH:
                    raise ValueError(f'Tag exceeds max length ({MAX_TAG_LENGTH}): {tag_clean[:50]}...')
                validated_tags.append(tag_clean)

        return validated_tags

    @field_validator('salary_max')
    @classmethod
    def validate_salary_range(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure salary_max >= salary_min if both are provided"""
        if v is not None and 'salary_min' in info.data:
            salary_min = info.data['salary_min']
            if salary_min is not None and v < salary_min:
                raise ValueError(f'salary_max ({v}) must be >= salary_min ({salary_min})')
        return v

    @field_validator('raw_data')
    @classmethod
    def sanitize_raw_data(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Sanitize raw_data to prevent XSS attacks"""
        if v is None:
            return None
        return sanitize_html_content(v)

    @field_validator('title', 'company', 'description')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from text fields"""
        return v.strip()

    class Config:
        str_strip_whitespace = True


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
    salary_currency: Optional[str] = None
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
