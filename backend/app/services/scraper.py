"""
Job scraper service - handles saving scraped jobs to database
"""
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.job import Job
from app.models.scrape_log import ScrapeLog


class ScraperService:
    """Service for handling job scraping operations"""

    def __init__(self, db: Session):
        self.db = db

    def save_jobs(
        self, jobs: List[Dict[str, Any]], source: str, scrape_log_id: int | None = None
    ) -> Dict[str, int]:
        """
        Save jobs to database with deduplication.

        Uses PostgreSQL's ON CONFLICT to update existing jobs or insert new ones.
        Deduplication is based on (source, source_id) unique constraint.

        Args:
            jobs: List of job dictionaries from scraper
            source: Source name (e.g., "remoteok")
            scrape_log_id: Optional scrape log ID to track this operation

        Returns:
            Dictionary with counts: {"total": int, "new": int, "updated": int}
        """
        if not jobs:
            return {"total": 0, "new": 0, "updated": 0}

        total = len(jobs)
        new_count = 0
        updated_count = 0

        for job_data in jobs:
            # Ensure source is set
            job_data["source"] = source

            # Convert tags list to proper format
            if "tags" in job_data and isinstance(job_data["tags"], list):
                job_data["tags"] = job_data["tags"]

            # Set scraped_at timestamp
            job_data["scraped_at"] = datetime.utcnow()

            # Use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE
            # This provides atomic upsert functionality
            stmt = insert(Job).values(**job_data)

            # Define what to update if conflict occurs
            update_dict = {
                "title": stmt.excluded.title,
                "company": stmt.excluded.company,
                "description": stmt.excluded.description,
                "salary_min": stmt.excluded.salary_min,
                "salary_max": stmt.excluded.salary_max,
                "salary_currency": stmt.excluded.salary_currency,
                "location": stmt.excluded.location,
                "remote_type": stmt.excluded.remote_type,
                "job_type": stmt.excluded.job_type,
                "tags": stmt.excluded.tags,
                "raw_data": stmt.excluded.raw_data,
                "scraped_at": stmt.excluded.scraped_at,
                "updated_at": datetime.utcnow(),
            }

            stmt = stmt.on_conflict_do_update(
                index_elements=["source", "source_id"],
                set_=update_dict,
            )

            # Execute and check if it was an insert or update
            # We'll track this by checking if the job existed before
            existing_job = (
                self.db.query(Job)
                .filter(
                    Job.source == job_data["source"],
                    Job.source_id == job_data["source_id"],
                )
                .first()
            )

            self.db.execute(stmt)

            if existing_job:
                updated_count += 1
            else:
                new_count += 1

        self.db.commit()

        return {
            "total": total,
            "new": new_count,
            "updated": updated_count,
        }

    def get_job_by_source_id(self, source: str, source_id: str) -> Job | None:
        """Get job by source and source_id"""
        return (
            self.db.query(Job)
            .filter(Job.source == source, Job.source_id == source_id)
            .first()
        )

    def get_recent_jobs(self, source: str | None = None, limit: int = 50) -> List[Job]:
        """Get recent jobs, optionally filtered by source"""
        query = self.db.query(Job).order_by(Job.scraped_at.desc())

        if source:
            query = query.filter(Job.source == source)

        return query.limit(limit).all()

    def create_scrape_log(self, source: str) -> ScrapeLog:
        """Create a new scrape log entry"""
        scrape_log = ScrapeLog(source=source, status="running")
        self.db.add(scrape_log)
        self.db.commit()
        self.db.refresh(scrape_log)
        return scrape_log

    def update_scrape_log(
        self,
        scrape_log_id: int,
        status: str,
        jobs_found: int = 0,
        jobs_new: int = 0,
        error: str | None = None,
    ) -> None:
        """Update a scrape log with results"""
        scrape_log = self.db.query(ScrapeLog).filter(ScrapeLog.id == scrape_log_id).first()
        if scrape_log:
            scrape_log.status = status
            scrape_log.jobs_found = jobs_found
            scrape_log.jobs_new = jobs_new
            scrape_log.completed_at = datetime.utcnow()
            if error:
                scrape_log.error = error
            self.db.commit()
