"""
Unit tests for job scrapers
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone


class TestRemoteOKScraper:
    """Tests for RemoteOK scraper"""

    @pytest.mark.asyncio
    async def test_normalize_job(self):
        """Test job normalization"""
        from app.scrapers.remoteok import normalize_job

        raw_job = {
            "id": "123456",
            "position": "Senior Python Developer",
            "company": "TestCorp",
            "description": "We need a Python developer",
            "url": "https://remoteok.com/jobs/123456",
            "salary_min": "100000",
            "salary_max": "150000",
            "location": "Worldwide",
            "tags": ["python", "django", "aws"],
            "date": "2025-12-01T00:00:00Z"
        }

        job = normalize_job(raw_job)

        assert job["source"] == "remoteok"
        assert job["source_id"] == "123456"
        assert job["title"] == "Senior Python Developer"
        assert job["company"] == "TestCorp"
        assert job["salary_min"] == 100000
        assert job["salary_max"] == 150000
        assert job["tags"] == ["python", "django", "aws"]

    def test_detect_job_type(self):
        """Test job type detection"""
        from app.scrapers.remoteok import detect_job_type

        assert detect_job_type({"position": "Contract Developer", "description": ""}) == "contract"
        assert detect_job_type({"position": "Freelance Designer", "description": ""}) == "contract"
        assert detect_job_type({"position": "Part-time Engineer", "description": ""}) == "part-time"
        assert detect_job_type({"position": "Software Engineer", "description": ""}) == "permanent"


class TestWeWorkRemotelyScraper:
    """Tests for We Work Remotely scraper"""

    def test_clean_html(self):
        """Test HTML cleaning"""
        from app.scrapers.weworkremotely import clean_html

        html = "<p>Hello <strong>World</strong></p><br>Test"
        result = clean_html(html)
        assert "Hello" in result
        assert "World" in result
        assert "<" not in result

    def test_extract_salary(self):
        """Test salary extraction"""
        from app.scrapers.weworkremotely import extract_salary

        # Test $100k - $150k format
        min_sal, max_sal = extract_salary("Salary: $100k - $150k per year")
        assert min_sal == 100000
        assert max_sal == 150000

        # Test $100,000 - $150,000 format
        min_sal, max_sal = extract_salary("$100,000 - $150,000")
        assert min_sal == 100000
        assert max_sal == 150000

        # Test no salary
        min_sal, max_sal = extract_salary("No salary info here")
        assert min_sal is None
        assert max_sal is None

    def test_detect_job_type(self):
        """Test job type detection"""
        from app.scrapers.weworkremotely import detect_job_type

        assert detect_job_type("Contract Developer", "") == "contract"
        assert detect_job_type("", "Looking for freelance work") == "contract"
        assert detect_job_type("Part-time role", "") == "part-time"
        assert detect_job_type("Software Engineer", "Full time position") == "permanent"


class TestHackerNewsScraper:
    """Tests for HackerNews scraper"""

    def test_clean_html(self):
        """Test HTML cleaning"""
        from app.scrapers.hackernews import clean_html

        html = "<p>Job description</p><br><p>Requirements</p>"
        result = clean_html(html)
        assert "Job description" in result
        assert "Requirements" in result
        assert "<" not in result

    def test_extract_salary(self):
        """Test salary extraction"""
        from app.scrapers.hackernews import extract_salary

        # Test various formats
        min_sal, max_sal = extract_salary("$120k-$180k")
        assert min_sal == 120000
        assert max_sal == 180000

        min_sal, max_sal = extract_salary("100k - 150k compensation")
        assert min_sal == 100000
        assert max_sal == 150000

    def test_extract_tech_tags(self):
        """Test tech tag extraction"""
        from app.scrapers.hackernews import extract_tech_tags

        text = "We use Python, React, and AWS for our stack. Experience with Docker required."
        tags = extract_tech_tags(text)

        assert "python" in tags
        assert "react" in tags
        assert "aws" in tags
        assert "docker" in tags

    def test_detect_job_type(self):
        """Test job type detection"""
        from app.scrapers.hackernews import detect_job_type

        assert detect_job_type("Contract position", "") == "contract"
        assert detect_job_type("", "Looking for freelance consultant") == "contract"
        assert detect_job_type("", "Internship opportunity") == "internship"
        assert detect_job_type("Senior Engineer", "Full time role") == "permanent"
