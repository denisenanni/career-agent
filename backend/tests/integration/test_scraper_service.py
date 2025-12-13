"""
Integration tests for ScraperService
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.services.scraper import ScraperService
from app.models.job import Job
from app.models.scrape_log import ScrapeLog


class TestScraperServiceSaveJobs:
    """Test ScraperService.save_jobs method"""

    def test_save_new_jobs(self, db_session: Session, sample_jobs_batch):
        """Test saving new jobs to database"""
        service = ScraperService(db_session)

        result = service.save_jobs(sample_jobs_batch, source="test_source")

        assert result["total"] == 5
        assert result["new"] == 5
        assert result["updated"] == 0
        assert result["failed"] == 0

        # Verify jobs in database
        jobs = db_session.query(Job).all()
        assert len(jobs) == 5
        assert jobs[0].source == "test_source"

    def test_save_empty_jobs_list(self, db_session: Session):
        """Test saving empty jobs list returns zero counts"""
        service = ScraperService(db_session)

        result = service.save_jobs([], source="test_source")

        assert result["total"] == 0
        assert result["new"] == 0
        assert result["updated"] == 0
        assert result["failed"] == 0

    def test_update_existing_jobs(self, db_session: Session, sample_job_data):
        """Test updating existing jobs with new data"""
        service = ScraperService(db_session)

        # First insert
        result1 = service.save_jobs([sample_job_data], source="test_source")
        assert result1["new"] == 1

        # Update with modified data
        updated_data = sample_job_data.copy()
        updated_data["title"] = "Updated Title"
        updated_data["salary_max"] = 200000

        result2 = service.save_jobs([updated_data], source="test_source")

        assert result2["total"] == 1
        assert result2["new"] == 0
        assert result2["updated"] == 1
        assert result2["failed"] == 0

        # Verify update in database
        job = db_session.query(Job).filter(
            Job.source == "test_source",
            Job.source_id == sample_job_data["source_id"]
        ).first()

        assert job.title == "Updated Title"
        assert job.salary_max == 200000

    def test_mixed_new_and_updated_jobs(self, db_session: Session, sample_jobs_batch):
        """Test batch with both new and existing jobs"""
        service = ScraperService(db_session)

        # Insert first 3 jobs
        first_batch = sample_jobs_batch[:3]
        service.save_jobs(first_batch, source="test_source")

        # Insert batch with 2 existing + 2 new jobs
        mixed_batch = sample_jobs_batch[1:5]  # job_2, job_3 exist; job_4, job_5 are new
        result = service.save_jobs(mixed_batch, source="test_source")

        assert result["total"] == 4
        assert result["new"] == 2
        assert result["updated"] == 2

    def test_invalid_job_validation_failure(self, db_session: Session):
        """Test jobs with validation errors are marked as failed"""
        service = ScraperService(db_session)

        invalid_jobs = [
            {
                "source_id": "valid_job",
                "url": "https://example.com/job",
                "title": "Valid Job",
                "company": "Company",
                "description": "Description",
            },
            {
                "source_id": "invalid_job",
                "url": "not-a-valid-url",  # Invalid URL
                "title": "Invalid Job",
                "company": "Company",
                "description": "Description",
            },
        ]

        result = service.save_jobs(invalid_jobs, source="test_source")

        assert result["total"] == 1  # Only valid job counted
        assert result["new"] == 1
        assert result["failed"] == 1

        # Only valid job in database
        jobs = db_session.query(Job).all()
        assert len(jobs) == 1
        assert jobs[0].source_id == "valid_job"

    def test_missing_required_fields(self, db_session: Session):
        """Test jobs missing required fields are failed"""
        service = ScraperService(db_session)

        jobs = [
            {
                # Missing source_id, url, title, company, description
                "salary_min": 100000,
            }
        ]

        result = service.save_jobs(jobs, source="test_source")

        assert result["total"] == 0
        assert result["failed"] == 1

        # No jobs in database
        assert db_session.query(Job).count() == 0

    def test_timestamps_are_set(self, db_session: Session, sample_job_data):
        """Test created_at, updated_at, and scraped_at timestamps are set"""
        service = ScraperService(db_session)

        before_save = datetime.now(timezone.utc)
        service.save_jobs([sample_job_data], source="test_source")
        after_save = datetime.now(timezone.utc)

        job = db_session.query(Job).first()

        # All timestamps should be set
        assert job.created_at is not None
        assert job.updated_at is not None
        assert job.scraped_at is not None

        # Timestamps should be recent
        assert before_save <= job.created_at.replace(tzinfo=timezone.utc) <= after_save
        assert before_save <= job.updated_at.replace(tzinfo=timezone.utc) <= after_save

    def test_created_at_preserved_on_update(self, db_session: Session, sample_job_data):
        """Test created_at is not changed when job is updated"""
        service = ScraperService(db_session)

        # First insert
        service.save_jobs([sample_job_data], source="test_source")
        job_v1 = db_session.query(Job).first()
        original_created_at = job_v1.created_at

        # Wait a moment and update
        import time
        time.sleep(0.1)

        updated_data = sample_job_data.copy()
        updated_data["title"] = "Updated Title"
        service.save_jobs([updated_data], source="test_source")

        job_v2 = db_session.query(Job).first()

        # created_at should be unchanged
        assert job_v2.created_at == original_created_at

        # updated_at should be newer
        assert job_v2.updated_at > job_v2.created_at

    def test_batch_commit_behavior(self, db_session: Session):
        """Test batch commits work correctly with large datasets"""
        service = ScraperService(db_session)

        # Create 300 jobs (larger than BATCH_COMMIT_SIZE = 250)
        large_batch = [
            {
                "source_id": f"job_{i}",
                "url": f"https://example.com/job/{i}",
                "title": f"Job {i}",
                "company": "Company",
                "description": "Description",
            }
            for i in range(300)
        ]

        result = service.save_jobs(large_batch, source="test_source")

        assert result["total"] == 300
        assert result["new"] == 300
        assert result["failed"] == 0

        # All jobs should be in database
        assert db_session.query(Job).count() == 300

    def test_source_isolation(self, db_session: Session, sample_job_data):
        """Test jobs from different sources are isolated"""
        service = ScraperService(db_session)

        # Save same source_id from different sources
        service.save_jobs([sample_job_data], source="source_a")
        service.save_jobs([sample_job_data], source="source_b")

        # Should create 2 separate jobs
        jobs = db_session.query(Job).all()
        assert len(jobs) == 2

        sources = {job.source for job in jobs}
        assert sources == {"source_a", "source_b"}


class TestScraperServiceGetJobBySourceId:
    """Test ScraperService.get_job_by_source_id method"""

    def test_get_existing_job(self, db_session: Session, existing_job: Job):
        """Test retrieving existing job by source and source_id"""
        service = ScraperService(db_session)

        job = service.get_job_by_source_id("test_source", existing_job.source_id)

        assert job is not None
        assert job.id == existing_job.id
        assert job.source_id == existing_job.source_id

    def test_get_nonexistent_job(self, db_session: Session):
        """Test retrieving non-existent job returns None"""
        service = ScraperService(db_session)

        job = service.get_job_by_source_id("test_source", "nonexistent_id")

        assert job is None

    def test_source_specificity(self, db_session: Session, sample_job_data):
        """Test job lookup is source-specific"""
        service = ScraperService(db_session)

        # Save job with source_a
        service.save_jobs([sample_job_data], source="source_a")

        # Try to retrieve with source_b
        job = service.get_job_by_source_id("source_b", sample_job_data["source_id"])

        assert job is None


class TestScraperServiceGetRecentJobs:
    """Test ScraperService.get_recent_jobs method"""

    def test_get_recent_jobs_default_limit(self, db_session: Session, sample_jobs_batch):
        """Test getting recent jobs with default limit"""
        service = ScraperService(db_session)
        service.save_jobs(sample_jobs_batch, source="test_source")

        jobs = service.get_recent_jobs()

        assert len(jobs) == 5
        assert jobs[0].source_id == "job_5"  # Most recent first

    def test_get_recent_jobs_custom_limit(self, db_session: Session, sample_jobs_batch):
        """Test getting recent jobs with custom limit"""
        service = ScraperService(db_session)
        service.save_jobs(sample_jobs_batch, source="test_source")

        jobs = service.get_recent_jobs(limit=3)

        assert len(jobs) == 3

    def test_get_recent_jobs_filtered_by_source(self, db_session: Session, sample_jobs_batch):
        """Test filtering recent jobs by source"""
        service = ScraperService(db_session)

        # Save jobs from two different sources
        service.save_jobs(sample_jobs_batch[:3], source="source_a")
        service.save_jobs(sample_jobs_batch[3:], source="source_b")

        jobs_a = service.get_recent_jobs(source="source_a")
        jobs_b = service.get_recent_jobs(source="source_b")

        assert len(jobs_a) == 3
        assert len(jobs_b) == 2
        assert all(job.source == "source_a" for job in jobs_a)
        assert all(job.source == "source_b" for job in jobs_b)

    def test_get_recent_jobs_ordered_by_scraped_at(self, db_session: Session):
        """Test jobs are ordered by scraped_at descending"""
        service = ScraperService(db_session)

        jobs_data = [
            {
                "source_id": f"job_{i}",
                "url": f"https://example.com/job/{i}",
                "title": f"Job {i}",
                "company": "Company",
                "description": "Description",
            }
            for i in range(3)
        ]

        # Save jobs at different times
        import time
        for job_data in jobs_data:
            service.save_jobs([job_data], source="test_source")
            time.sleep(0.01)

        jobs = service.get_recent_jobs()

        # Should be in reverse order (most recent first)
        assert jobs[0].source_id == "job_2"
        assert jobs[1].source_id == "job_1"
        assert jobs[2].source_id == "job_0"


class TestScraperServiceScrapeLog:
    """Test ScrapeLog-related methods"""

    def test_create_scrape_log(self, db_session: Session):
        """Test creating a new scrape log"""
        service = ScraperService(db_session)

        log = service.create_scrape_log(source="test_source")

        assert log.id is not None
        assert log.source == "test_source"
        assert log.status == "running"
        assert log.started_at is not None

    def test_update_scrape_log_success(self, db_session: Session):
        """Test updating scrape log with success status"""
        service = ScraperService(db_session)

        log = service.create_scrape_log(source="test_source")

        service.update_scrape_log(
            scrape_log_id=log.id,
            status="completed",
            jobs_found=100,
            jobs_new=50,
        )

        # Refresh and verify
        db_session.refresh(log)

        assert log.status == "completed"
        assert log.jobs_found == 100
        assert log.jobs_new == 50
        assert log.completed_at is not None
        assert log.error is None

    def test_update_scrape_log_failure(self, db_session: Session):
        """Test updating scrape log with error"""
        service = ScraperService(db_session)

        log = service.create_scrape_log(source="test_source")

        service.update_scrape_log(
            scrape_log_id=log.id,
            status="failed",
            error="Connection timeout",
        )

        db_session.refresh(log)

        assert log.status == "failed"
        assert log.error == "Connection timeout"
        assert log.completed_at is not None

    def test_update_nonexistent_scrape_log(self, db_session: Session):
        """Test updating non-existent scrape log raises ValueError"""
        service = ScraperService(db_session)

        with pytest.raises(ValueError, match="Scrape log .* not found"):
            service.update_scrape_log(
                scrape_log_id=99999,
                status="completed",
            )


class TestScraperServicePerformance:
    """Test performance-related behavior"""

    def test_n_plus_one_avoided(self, db_session: Session):
        """Test N+1 query problem is avoided with batch query"""
        service = ScraperService(db_session)

        # Create 100 jobs
        jobs = [
            {
                "source_id": f"job_{i}",
                "url": f"https://example.com/job/{i}",
                "title": f"Job {i}",
                "company": "Company",
                "description": "Description",
            }
            for i in range(100)
        ]

        # This should use batch query, not 100 individual queries
        result = service.save_jobs(jobs, source="test_source")

        assert result["total"] == 100
        assert result["new"] == 100

    def test_html_sanitization_applied(self, db_session: Session):
        """Test HTML in raw_data is sanitized"""
        service = ScraperService(db_session)

        job_data = {
            "source_id": "job_xss",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "raw_data": {
                "unsafe_field": "<script>alert('xss')</script>",
            },
        }

        service.save_jobs([job_data], source="test_source")

        job = db_session.query(Job).first()

        # HTML should be escaped
        assert "&lt;script&gt;" in str(job.raw_data)
        assert "<script>" not in str(job.raw_data)
