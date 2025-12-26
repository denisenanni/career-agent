"""
Integration tests for Jobs Router
"""
import pytest
import os
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

from app.main import app
from app.models.job import Job
from app.database import get_db

# Skip PostgreSQL-specific tests if using SQLite
requires_postgresql = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Requires PostgreSQL (full-text search not supported in SQLite)"
)


@pytest.fixture
def sample_jobs(db_session: Session):
    """Create sample jobs in the database"""
    jobs = [
        Job(
            source="remoteok",
            source_id="job_1",
            url="https://remoteok.com/job/1",
            title="Senior Python Developer",
            company="TechCorp",
            description="Great opportunity for a Python developer. Work on exciting projects with modern stack.",
            salary_min=120000,
            salary_max=180000,
            salary_currency="USD",
            location="Remote",
            remote_type="full",
            job_type="permanent",
            tags=["python", "django", "aws"],
            scraped_at=datetime.now(timezone.utc),
        ),
        Job(
            source="weworkremotely",
            source_id="job_2",
            url="https://weworkremotely.com/job/2",
            title="Frontend Developer",
            company="StartupInc",
            description="Looking for a skilled frontend developer to join our team.",
            salary_min=90000,
            salary_max=130000,
            salary_currency="USD",
            location="San Francisco, CA",
            remote_type="hybrid",
            job_type="contract",
            tags=["react", "typescript"],
            scraped_at=datetime.now(timezone.utc),
        ),
        Job(
            source="remoteok",
            source_id="job_3",
            url="https://remoteok.com/job/3",
            title="DevOps Engineer",
            company="CloudServices",
            description="DevOps engineer needed for cloud infrastructure management.",
            salary_min=110000,
            salary_max=160000,
            salary_currency="USD",
            location="Remote",
            remote_type="full",
            job_type="permanent",
            tags=["kubernetes", "docker", "aws"],
            scraped_at=datetime.now(timezone.utc),
        ),
    ]

    for job in jobs:
        db_session.add(job)
    db_session.commit()

    return jobs


class TestListJobs:
    """Test GET /api/jobs endpoint"""

    def test_list_all_jobs(self, client, sample_jobs):
        """Test listing all jobs without filters"""
        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 3
        assert len(data["jobs"]) == 3
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 20

    def test_list_jobs_with_pagination(self, client, sample_jobs):
        """Test pagination with page and per_page"""
        response = client.get("/api/jobs?page=1&per_page=2")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 3
        assert len(data["jobs"]) == 2
        assert data["pagination"]["per_page"] == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["has_next"] is True

    def test_filter_by_source(self, client, sample_jobs):
        """Test filtering jobs by source"""
        response = client.get("/api/jobs?source=remoteok")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 2
        assert all(job["source"] == "remoteok" for job in data["jobs"])

    def test_filter_by_job_type(self, client, sample_jobs):
        """Test filtering jobs by job_type"""
        response = client.get("/api/jobs?job_type=permanent")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 2
        assert all(job["job_type"] == "permanent" for job in data["jobs"])

    def test_filter_by_remote_type(self, client, sample_jobs):
        """Test filtering jobs by remote_type"""
        response = client.get("/api/jobs?remote_type=full")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 2
        assert all(job["remote_type"] == "full" for job in data["jobs"])

    def test_filter_by_min_salary(self, client, sample_jobs):
        """Test filtering jobs by minimum salary"""
        response = client.get("/api/jobs?min_salary=110000")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 2
        for job in data["jobs"]:
            assert job["salary_min"] >= 110000

    @requires_postgresql
    def test_search_in_title(self, client, sample_jobs):
        """Test searching in job title"""
        response = client.get("/api/jobs?search=Python")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 1
        assert "Python" in data["jobs"][0]["title"]

    @requires_postgresql
    def test_search_in_company(self, client, sample_jobs):
        """Test searching in company name"""
        response = client.get("/api/jobs?search=TechCorp")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 1
        assert data["jobs"][0]["company"] == "TechCorp"

    @requires_postgresql
    def test_search_in_description(self, client, sample_jobs):
        """Test searching in job description"""
        response = client.get("/api/jobs?search=infrastructure")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 1
        assert "infrastructure" in data["jobs"][0]["description"].lower()

    @requires_postgresql
    def test_search_escapes_sql_wildcards(self, client, sample_jobs):
        """Test that SQL wildcards in search are escaped"""
        response = client.get("/api/jobs?search=%_malicious")

        assert response.status_code == 200
        data = response.json()

        # Should find no results since wildcards are escaped
        assert data["pagination"]["total"] == 0

    def test_multiple_filters_combined(self, client, sample_jobs):
        """Test combining multiple filters"""
        response = client.get("/api/jobs?source=remoteok&remote_type=full&min_salary=100000")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 2
        for job in data["jobs"]:
            assert job["source"] == "remoteok"
            assert job["remote_type"] == "full"
            assert job["salary_min"] >= 100000

    @requires_postgresql
    def test_filter_by_single_skill(self, client, sample_jobs):
        """Test filtering jobs by single skill"""
        response = client.get("/api/jobs?skills=python")

        assert response.status_code == 200
        data = response.json()

        # Only the Python Developer job has "python" tag
        assert data["pagination"]["total"] >= 1
        for job in data["jobs"]:
            assert any("python" in tag.lower() for tag in job["tags"])

    @requires_postgresql
    def test_filter_by_multiple_skills(self, client, sample_jobs):
        """Test filtering jobs by multiple skills (OR logic)"""
        response = client.get("/api/jobs?skills=python,react")

        assert response.status_code == 200
        data = response.json()

        # Should find jobs with either python OR react
        assert data["pagination"]["total"] >= 2
        for job in data["jobs"]:
            job_tags_lower = [tag.lower() for tag in job["tags"]]
            assert "python" in job_tags_lower or "react" in job_tags_lower

    @requires_postgresql
    def test_filter_by_skill_case_insensitive(self, client, sample_jobs):
        """Test that skill filter is case insensitive"""
        response_lower = client.get("/api/jobs?skills=python")
        response_upper = client.get("/api/jobs?skills=PYTHON")

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200

        # Both should find the same jobs
        assert response_lower.json()["pagination"]["total"] == response_upper.json()["pagination"]["total"]

    @requires_postgresql
    def test_filter_skills_with_search(self, client, sample_jobs):
        """Test combining skills filter with search"""
        response = client.get("/api/jobs?skills=python&search=Developer")

        assert response.status_code == 200
        data = response.json()

        # Should find Python Developer job
        assert data["pagination"]["total"] >= 1
        for job in data["jobs"]:
            assert any("python" in tag.lower() for tag in job["tags"])

    @requires_postgresql
    def test_description_is_truncated(self, client, sample_jobs):
        """Test that long descriptions are truncated in list view"""
        # Create a job with very long description
        long_desc_job = Job(
            source="remoteok",
            source_id="long_desc_job",
            url="https://remoteok.com/job/long",
            title="Test Job",
            company="Test Company",
            description="x" * 600,  # Longer than default truncate length (500)
            scraped_at=datetime.now(timezone.utc),
        )
        db_session = next(app.dependency_overrides[get_db]())
        db_session.add(long_desc_job)
        db_session.commit()

        response = client.get("/api/jobs?search=Test")

        assert response.status_code == 200
        data = response.json()

        # Find the job with long description
        test_job = next(job for job in data["jobs"] if job["title"] == "Test Job")

        # Should be truncated to 500 chars + "..."
        assert len(test_job["description"]) == 503
        assert test_job["description"].endswith("...")

    def test_per_page_validation(self, client):
        """Test per_page parameter validation"""
        # per_page too high
        response = client.get("/api/jobs?per_page=101")
        assert response.status_code == 422

        # per_page too low
        response = client.get("/api/jobs?per_page=0")
        assert response.status_code == 422

    def test_page_validation(self, client):
        """Test page parameter validation"""
        # Page must be >= 1
        response = client.get("/api/jobs?page=0")
        assert response.status_code == 422

    @requires_postgresql
    def test_empty_results(self, client):
        """Test response when no jobs match filters"""
        response = client.get("/api/jobs?search=nonexistent")

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["total"] == 0
        assert data["jobs"] == []

    def test_jobs_ordered_by_scraped_at_desc(self, client, sample_jobs):
        """Test that jobs are ordered by scraped_at descending"""
        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()

        # Check that jobs are in descending order by scraped_at
        scraped_dates = [job["scraped_at"] for job in data["jobs"]]
        assert scraped_dates == sorted(scraped_dates, reverse=True)


class TestGetJob:
    """Test GET /api/jobs/{job_id} endpoint"""

    def test_get_existing_job(self, client, sample_jobs):
        """Test retrieving an existing job by ID"""
        job_id = sample_jobs[0].id

        response = client.get(f"/api/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == job_id
        assert data["title"] == "Senior Python Developer"
        assert data["company"] == "TechCorp"
        # Full description should be returned (not truncated)
        assert not data["description"].endswith("...")

    def test_get_job_with_full_description(self, client, sample_jobs):
        """Test that full description is returned (not truncated)"""
        # Create job with long description
        long_desc_job = Job(
            source="remoteok",
            source_id="long_desc_detail",
            url="https://remoteok.com/job/detail",
            title="Detail Test",
            company="Test Co",
            description="x" * 600,
            scraped_at=datetime.now(timezone.utc),
        )
        db_session = next(app.dependency_overrides[get_db]())
        db_session.add(long_desc_job)
        db_session.commit()

        response = client.get(f"/api/jobs/{long_desc_job.id}")

        assert response.status_code == 200
        data = response.json()

        # Full description should be 600 chars
        assert len(data["description"]) == 600
        assert not data["description"].endswith("...")

    def test_get_nonexistent_job(self, client):
        """Test retrieving a job that doesn't exist"""
        response = client.get("/api/jobs/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"

    def test_get_job_includes_raw_data(self, client, sample_jobs):
        """Test that raw_data is included in job detail"""
        job_id = sample_jobs[0].id

        response = client.get(f"/api/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        # raw_data field should be present
        assert "raw_data" in data


class TestScrapeJobs:
    """Test POST /api/jobs/scrape endpoint (API key auth)"""

    @patch('app.routers.jobs.settings')
    def test_scrape_jobs_no_api_key(self, mock_settings, client):
        """Test that scrape endpoint rejects requests without API key"""
        mock_settings.scraper_api_key = "configured-key"

        response = client.post("/api/jobs/scrape")

        assert response.status_code == 401
        assert "X-API-Key header required" in response.json()["detail"]

    @patch('app.routers.jobs.settings')
    def test_scrape_jobs_invalid_api_key(self, mock_settings, client):
        """Test that scrape endpoint rejects invalid API key"""
        mock_settings.scraper_api_key = "correct-key"

        response = client.post(
            "/api/jobs/scrape",
            headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @patch('app.routers.jobs.settings')
    def test_scrape_jobs_no_key_configured(self, mock_settings, client):
        """Test that scrape endpoint fails if SCRAPER_API_KEY not configured"""
        mock_settings.scraper_api_key = ""

        response = client.post(
            "/api/jobs/scrape",
            headers={"X-API-Key": "some-key"}
        )

        assert response.status_code == 500
        assert "not configured" in response.json()["detail"]

    @patch('app.routers.jobs.run_scraper', new_callable=AsyncMock)
    @patch('app.routers.jobs.settings')
    def test_scrape_jobs_success(self, mock_settings, mock_run_scraper, client):
        """Test successful scrape with valid API key"""
        mock_settings.scraper_api_key = "test-scraper-key"
        mock_run_scraper.return_value = {
            "remoteok": {"total": 10, "new": 5},
            "weworkremotely": {"total": 8, "new": 3}
        }

        response = client.post(
            "/api/jobs/scrape",
            headers={"X-API-Key": "test-scraper-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert "stats" in data
        mock_run_scraper.assert_called_once()


class TestRefreshJobs:
    """Test POST /api/jobs/refresh endpoint"""

    @patch('app.routers.jobs.run_scraper')
    def test_refresh_jobs_queues_background_task(self, mock_run_scraper, authenticated_client):
        """Test that refresh endpoint queues a background task (requires auth)"""
        response = authenticated_client.post("/api/jobs/refresh")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "queued"
        assert "background" in data["message"].lower()


class TestGetLatestScrapeLogs:
    """Test GET /api/jobs/logs/latest endpoint"""

    def test_get_latest_logs_empty(self, client):
        """Test getting logs when none exist"""
        response = client.get("/api/jobs/logs/latest")

        assert response.status_code == 200
        data = response.json()

        assert data["logs"] == []

    def test_get_latest_logs_with_limit(self, client):
        """Test limit parameter for logs"""
        response = client.get("/api/jobs/logs/latest?limit=5")

        assert response.status_code == 200

    def test_limit_validation_for_logs(self, client):
        """Test limit validation for logs endpoint"""
        # Limit too high
        response = client.get("/api/jobs/logs/latest?limit=51")
        assert response.status_code == 422

        # Limit too low
        response = client.get("/api/jobs/logs/latest?limit=0")
        assert response.status_code == 422


class TestRunScraperErrorHandling:
    """Test run_scraper function error handling for individual scrapers"""

    @pytest.mark.asyncio
    @patch('app.scrapers.remoteok.scrape_and_save')
    async def test_run_scraper_remoteok_failure(self, mock_remoteok):
        """Test that run_scraper continues when remoteok scraper fails"""
        from app.routers.jobs import run_scraper

        # Mock remoteok to fail
        mock_remoteok.side_effect = Exception("RemoteOK API error")

        result = await run_scraper()

        # Should have error for remoteok
        assert "remoteok" in result
        assert "error" in result["remoteok"]
        assert "RemoteOK API error" in result["remoteok"]["error"]

    @pytest.mark.asyncio
    @patch('app.scrapers.weworkremotely.scrape_and_save')
    async def test_run_scraper_weworkremotely_failure(self, mock_wwr):
        """Test that run_scraper continues when weworkremotely scraper fails"""
        from app.routers.jobs import run_scraper

        # Mock weworkremotely to fail
        mock_wwr.side_effect = Exception("WeWorkRemotely connection timeout")

        result = await run_scraper()

        # Should have error for weworkremotely
        assert "weworkremotely" in result
        assert "error" in result["weworkremotely"]
        assert "WeWorkRemotely connection timeout" in result["weworkremotely"]["error"]

    @pytest.mark.asyncio
    @patch('app.scrapers.hackernews.scrape_and_save')
    async def test_run_scraper_hackernews_failure(self, mock_hn):
        """Test that run_scraper continues when hackernews scraper fails"""
        from app.routers.jobs import run_scraper

        # Mock hackernews to fail
        mock_hn.side_effect = Exception("HackerNews API rate limit")

        result = await run_scraper()

        # Should have error for hackernews
        assert "hackernews" in result
        assert "error" in result["hackernews"]
        assert "HackerNews API rate limit" in result["hackernews"]["error"]

    @pytest.mark.asyncio
    @patch('app.scrapers.jobicy.scrape_and_save')
    async def test_run_scraper_jobicy_failure(self, mock_jobicy):
        """Test that run_scraper continues when jobicy scraper fails"""
        from app.routers.jobs import run_scraper

        # Mock jobicy to fail
        mock_jobicy.side_effect = Exception("Jobicy parse error")

        result = await run_scraper()

        # Should have error for jobicy
        assert "jobicy" in result
        assert "error" in result["jobicy"]
        assert "Jobicy parse error" in result["jobicy"]["error"]

    @pytest.mark.asyncio
    @patch('app.scrapers.remoteok.scrape_and_save')
    @patch('app.scrapers.weworkremotely.scrape_and_save')
    @patch('app.scrapers.hackernews.scrape_and_save')
    @patch('app.scrapers.jobicy.scrape_and_save')
    async def test_run_scraper_partial_failure(self, mock_jobicy, mock_hn, mock_wwr, mock_remoteok):
        """Test run_scraper with some scrapers succeeding and some failing"""
        from app.routers.jobs import run_scraper

        # Mock some to succeed and some to fail
        mock_remoteok.return_value = {"total": 10, "new": 5}
        mock_wwr.side_effect = Exception("WWR failed")
        mock_hn.return_value = {"total": 8, "new": 3}
        mock_jobicy.side_effect = Exception("Jobicy failed")

        result = await run_scraper()

        # Check successes
        assert result["remoteok"] == {"total": 10, "new": 5}
        assert result["hackernews"] == {"total": 8, "new": 3}

        # Check failures
        assert "error" in result["weworkremotely"]
        assert "error" in result["jobicy"]


class TestHelperFunctions:
    """Test helper functions used in the router"""

    def test_truncate_description_short_text(self):
        """Test truncate function with short text"""
        from app.routers.jobs import truncate_description

        text = "Short description"
        result = truncate_description(text)

        assert result == text
        assert not result.endswith("...")

    def test_truncate_description_long_text(self):
        """Test truncate function with long text"""
        from app.routers.jobs import truncate_description

        text = "x" * 600
        result = truncate_description(text, max_length=500)

        assert len(result) == 503  # 500 + "..."
        assert result.endswith("...")

    def test_escape_sql_wildcards_percent(self):
        """Test escaping percent wildcard"""
        from app.routers.jobs import escape_sql_wildcards

        result = escape_sql_wildcards("test%value")
        assert result == "test\\%value"

    def test_escape_sql_wildcards_underscore(self):
        """Test escaping underscore wildcard"""
        from app.routers.jobs import escape_sql_wildcards

        result = escape_sql_wildcards("test_value")
        assert result == "test\\_value"

    def test_escape_sql_wildcards_both(self):
        """Test escaping both wildcards"""
        from app.routers.jobs import escape_sql_wildcards

        result = escape_sql_wildcards("%_both_%")
        assert result == "\\%\\_both\\_\\%"

    def test_escape_sql_wildcards_safe_text(self):
        """Test that safe text is unchanged"""
        from app.routers.jobs import escape_sql_wildcards

        result = escape_sql_wildcards("safe text")
        assert result == "safe text"
