"""
Job scraper service - handles saving scraped jobs to database
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from pydantic import ValidationError
import logging

from app.models.job import Job
from app.models.scrape_log import ScrapeLog
from app.schemas.job import JobScrapedData

logger = logging.getLogger(__name__)

# Constants
DEFAULT_JOBS_LIMIT = 50
BATCH_COMMIT_SIZE = 250  # Optimized batch size: balances throughput vs memory/rollback risk


class ScraperService:
    """Service for handling job scraping operations"""

    def __init__(self, db: Session):
        self.db = db

    def save_jobs(
        self, jobs: List[Dict[str, Any]], source: str
    ) -> Dict[str, int]:
        """
        Save jobs to database with deduplication and validation.

        Uses PostgreSQL's ON CONFLICT to update existing jobs or insert new ones.
        Deduplication is based on (source, source_id) unique constraint.
        Implements batch commits for better error recovery.

        Args:
            jobs: List of job dictionaries from scraper
            source: Source name (e.g., "remoteok")

        Returns:
            Dictionary with counts: {"total": int, "new": int, "updated": int, "failed": int}
        """
        if not jobs:
            logger.info(f"No jobs to save from source: {source}")
            return {"total": 0, "new": 0, "updated": 0, "failed": 0}

        total = len(jobs)
        new_count = 0
        updated_count = 0
        failed_count = 0
        validation_failed_count = 0

        # Calculate timestamp once for all jobs
        now = datetime.now(timezone.utc)

        logger.info(f"Saving {total} jobs from source: {source}")

        # Batch query: Get all existing jobs in one query (fixes N+1 problem)
        source_ids = [job.get("source_id") for job in jobs if job.get("source_id")]
        existing_source_ids = set()

        if source_ids:
            try:
                existing_jobs = (
                    self.db.query(Job.source_id)
                    .filter(Job.source == source, Job.source_id.in_(source_ids))
                    .all()
                )
                existing_source_ids = {row[0] for row in existing_jobs}
                logger.debug(f"Found {len(existing_source_ids)} existing jobs in database")
            except Exception as e:
                logger.error(f"Failed to query existing jobs: {e}", exc_info=True)
                raise

        # Track successful inserts/updates for batch commit
        batch_count = 0

        for idx, job_data in enumerate(jobs):
            try:
                # Validate job data using Pydantic schema
                validated_job = JobScrapedData(**job_data)

                # Convert validated model to dict
                job_dict = validated_job.model_dump()

                # Ensure source is set
                job_dict["source"] = source

                # Set timestamps
                job_dict["scraped_at"] = now
                job_dict["created_at"] = now  # Will be used only on INSERT
                job_dict["updated_at"] = now  # Will be used on INSERT and UPDATE

                # Use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE
                # This provides atomic upsert functionality
                stmt = insert(Job).values(**job_dict)

                # Define what to update if conflict occurs
                # Note: created_at is NOT in update_dict, preserving original value
                update_dict = {
                    "title": stmt.excluded.title,
                    "company": stmt.excluded.company,
                    "description": stmt.excluded.description,
                    "url": stmt.excluded.url,
                    "salary_min": stmt.excluded.salary_min,
                    "salary_max": stmt.excluded.salary_max,
                    "salary_currency": stmt.excluded.salary_currency,
                    "location": stmt.excluded.location,
                    "remote_type": stmt.excluded.remote_type,
                    "job_type": stmt.excluded.job_type,
                    "tags": stmt.excluded.tags,
                    "posted_at": stmt.excluded.posted_at,
                    "raw_data": stmt.excluded.raw_data,
                    "scraped_at": stmt.excluded.scraped_at,
                    "updated_at": now,  # Always update timestamp on conflict
                }

                stmt = stmt.on_conflict_do_update(
                    index_elements=["source", "source_id"],
                    set_=update_dict,
                )

                self.db.execute(stmt)

                # Track if this was new or updated based on pre-fetched data
                if validated_job.source_id in existing_source_ids:
                    updated_count += 1
                else:
                    new_count += 1

                batch_count += 1

                # Batch commit for better error recovery
                if batch_count >= BATCH_COMMIT_SIZE:
                    try:
                        self.db.commit()
                        logger.debug(f"Batch committed {batch_count} jobs (progress: {idx + 1}/{total})")
                        batch_count = 0
                    except Exception as commit_error:
                        self.db.rollback()
                        logger.error(
                            f"Batch commit failed at job {idx + 1}/{total}: {commit_error}",
                            exc_info=True
                        )
                        # Continue processing remaining jobs
                        batch_count = 0

            except ValidationError as ve:
                if logger.isEnabledFor(logging.WARNING):
                    logger.warning(
                        f"Validation failed for job {job_data.get('source_id', 'unknown')}: {ve}"
                    )
                validation_failed_count += 1
                failed_count += 1
                continue
            except Exception as e:
                if logger.isEnabledFor(logging.WARNING):
                    logger.warning(
                        f"Failed to save job {job_data.get('source_id', 'unknown')}: {e}"
                    )
                failed_count += 1
                continue

        # Final commit for remaining jobs in batch
        if batch_count > 0:
            try:
                self.db.commit()
                logger.debug(f"Final batch committed {batch_count} jobs")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Final batch commit failed: {e}", exc_info=True)
                raise

        logger.info(
            f"Completed saving jobs from {source}: "
            f"{new_count} new, {updated_count} updated, "
            f"{failed_count} failed (including {validation_failed_count} validation failures)"
        )

        return {
            "total": total - failed_count,
            "new": new_count,
            "updated": updated_count,
            "failed": failed_count,
        }

    def get_job_by_source_id(self, source: str, source_id: str) -> Optional[Job]:
        """
        Get job by source and source_id.

        Args:
            source: Job source (e.g., "remoteok")
            source_id: External job ID from source

        Returns:
            Job object if found, None otherwise

        Raises:
            Exception if database query fails
        """
        try:
            return (
                self.db.query(Job)
                .filter(Job.source == source, Job.source_id == source_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Failed to get job {source}/{source_id}: {e}", exc_info=True)
            raise

    def get_recent_jobs(
        self, source: Optional[str] = None, limit: int = DEFAULT_JOBS_LIMIT
    ) -> List[Job]:
        """
        Get recent jobs, optionally filtered by source.

        Args:
            source: Optional source filter
            limit: Maximum number of jobs to return (default: DEFAULT_JOBS_LIMIT)

        Returns:
            List of Job objects ordered by scraped_at descending

        Raises:
            Exception if database query fails
        """
        try:
            query = self.db.query(Job).order_by(Job.scraped_at.desc())

            if source:
                query = query.filter(Job.source == source)

            return query.limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent jobs: {e}", exc_info=True)
            raise

    def create_scrape_log(self, source: str) -> ScrapeLog:
        """
        Create a new scrape log entry.

        Args:
            source: Job source being scraped

        Returns:
            Created ScrapeLog object

        Raises:
            Exception if creation fails
        """
        try:
            scrape_log = ScrapeLog(source=source, status="running")
            self.db.add(scrape_log)
            self.db.commit()
            self.db.refresh(scrape_log)
            logger.info(f"Created scrape log {scrape_log.id} for source: {source}")
            return scrape_log
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create scrape log for {source}: {e}")
            raise

    def update_scrape_log(
        self,
        scrape_log_id: int,
        status: str,
        jobs_found: int = 0,
        jobs_new: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """
        Update a scrape log with results.

        Args:
            scrape_log_id: ID of the scrape log to update
            status: New status (e.g., "completed", "failed")
            jobs_found: Total number of jobs found
            jobs_new: Number of new jobs added
            error: Optional error message if scrape failed

        Raises:
            ValueError if scrape log not found
        """
        try:
            scrape_log = self.db.query(ScrapeLog).filter(
                ScrapeLog.id == scrape_log_id
            ).first()

            if not scrape_log:
                error_msg = f"Scrape log {scrape_log_id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            scrape_log.status = status
            scrape_log.jobs_found = jobs_found
            scrape_log.jobs_new = jobs_new
            scrape_log.completed_at = datetime.now(timezone.utc)

            if error:
                scrape_log.error = error
                logger.warning(f"Scrape log {scrape_log_id} failed: {error}")
            else:
                logger.info(
                    f"Updated scrape log {scrape_log_id}: "
                    f"status={status}, found={jobs_found}, new={jobs_new}"
                )

            self.db.commit()

        except ValueError:
            # Re-raise ValueError for not found
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update scrape log {scrape_log_id}: {e}")
            raise
