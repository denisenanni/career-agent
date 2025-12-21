"""
Integration tests for Skills Router
"""
import os
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.job import Job
from app.models.custom_skill import CustomSkill


# Skip tests that require PostgreSQL-specific JSON functions
requires_postgres = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Requires PostgreSQL (TEST_DATABASE_URL not set)"
)


@pytest.fixture
def job_with_tags(db_session: Session):
    """Create a job with skill tags"""
    job = Job(
        source="test_source",
        source_id="test_job_skills_1",
        url="https://example.com/job/1",
        title="Python Developer",
        company="Test Company",
        description="Looking for a Python developer",
        tags=["Python", "Django", "PostgreSQL"],
        scraped_at=datetime.now(timezone.utc),
    )
    db_session.add(job)
    db_session.commit()
    return job


@pytest.fixture
def multiple_jobs_with_tags(db_session: Session):
    """Create multiple jobs with various skill tags"""
    jobs = [
        Job(
            source="test_source",
            source_id="test_job_skills_2",
            url="https://example.com/job/2",
            title="Backend Developer",
            company="Tech Corp",
            description="Backend role",
            tags=["Python", "FastAPI", "Redis"],
            scraped_at=datetime.now(timezone.utc),
        ),
        Job(
            source="test_source",
            source_id="test_job_skills_3",
            url="https://example.com/job/3",
            title="Data Engineer",
            company="Data Inc",
            description="Data role",
            tags=["Python", "SQL", "Spark"],
            scraped_at=datetime.now(timezone.utc),
        ),
        Job(
            source="test_source",
            source_id="test_job_skills_4",
            url="https://example.com/job/4",
            title="Frontend Developer",
            company="Web Corp",
            description="Frontend role",
            tags=["JavaScript", "React", "TypeScript"],
            scraped_at=datetime.now(timezone.utc),
        ),
    ]
    for job in jobs:
        db_session.add(job)
    db_session.commit()
    return jobs


@pytest.fixture
def custom_skill(db_session: Session):
    """Create a custom skill"""
    skill = CustomSkill(skill="Kubernetes", usage_count=5)
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)
    return skill


class TestGetPopularSkills:
    """Test GET /api/skills/popular endpoint"""

    def test_get_popular_skills_empty(self, client):
        """Test getting popular skills when no jobs exist"""
        response = client.get("/api/skills/popular")

        assert response.status_code == 200
        data = response.json()

        assert "skills" in data
        assert "total" in data
        assert isinstance(data["skills"], list)

    @requires_postgres
    def test_get_popular_skills_with_jobs(self, client, multiple_jobs_with_tags):
        """Test getting popular skills from job tags"""
        response = client.get("/api/skills/popular")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] > 0
        # Python appears in 2 jobs, should be popular
        assert "Python" in data["skills"]

    @requires_postgres
    def test_get_popular_skills_with_custom_skills(self, client, custom_skill):
        """Test that custom skills are included"""
        response = client.get("/api/skills/popular")

        assert response.status_code == 200
        data = response.json()

        assert "Kubernetes" in data["skills"]

    @requires_postgres
    def test_get_popular_skills_with_limit(self, client, multiple_jobs_with_tags):
        """Test limiting number of skills returned"""
        response = client.get("/api/skills/popular?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] <= 5

    @requires_postgres
    def test_get_popular_skills_filters_blacklist(self, client, db_session):
        """Test that blacklisted terms are filtered out"""
        # Create job with blacklisted tag
        job = Job(
            source="test_source",
            source_id="test_job_skills_blacklist",
            url="https://example.com/job/blacklist",
            title="Developer",
            company="Test",
            description="Test",
            tags=["developer", "Python", "engineer"],  # developer & engineer are blacklisted
            scraped_at=datetime.now(timezone.utc),
        )
        db_session.add(job)
        db_session.commit()

        response = client.get("/api/skills/popular")
        data = response.json()

        # Blacklisted terms should not appear
        skills_lower = [s.lower() for s in data["skills"]]
        assert "developer" not in skills_lower
        assert "engineer" not in skills_lower
        # But Python should be there
        assert "Python" in data["skills"]

    @requires_postgres
    def test_get_popular_skills_with_search(self, client, multiple_jobs_with_tags):
        """Test filtering skills by search term"""
        response = client.get("/api/skills/popular?search=Python")

        assert response.status_code == 200
        data = response.json()

        # Should only contain skills matching "Python"
        assert data["total"] >= 1
        assert "Python" in data["skills"]
        # Non-matching skills should not be present
        assert "JavaScript" not in data["skills"]
        assert "React" not in data["skills"]

    @requires_postgres
    def test_get_popular_skills_search_case_insensitive(self, client, multiple_jobs_with_tags):
        """Test that search is case insensitive"""
        response_lower = client.get("/api/skills/popular?search=python")
        response_upper = client.get("/api/skills/popular?search=PYTHON")

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200

        # Both should find Python
        assert "Python" in response_lower.json()["skills"]
        assert "Python" in response_upper.json()["skills"]

    @requires_postgres
    def test_get_popular_skills_search_partial_match(self, client, multiple_jobs_with_tags):
        """Test that search matches partial skill names"""
        response = client.get("/api/skills/popular?search=Script")

        assert response.status_code == 200
        data = response.json()

        # Should match both JavaScript and TypeScript
        skills = data["skills"]
        assert any("JavaScript" in s for s in skills) or any("TypeScript" in s for s in skills)

    @requires_postgres
    def test_get_popular_skills_search_custom_skill(self, client, custom_skill):
        """Test that search finds custom skills"""
        response = client.get("/api/skills/popular?search=Kube")

        assert response.status_code == 200
        data = response.json()

        assert "Kubernetes" in data["skills"]

    def test_get_popular_skills_search_no_match(self, client):
        """Test search with no matching skills"""
        response = client.get("/api/skills/popular?search=NonExistentSkill12345")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["skills"]) == 0

    def test_get_popular_skills_search_with_limit(self, client, multiple_jobs_with_tags):
        """Test combining search with limit"""
        response = client.get("/api/skills/popular?search=P&limit=10")

        assert response.status_code == 200
        data = response.json()

        # Should respect limit
        assert data["total"] <= 10


class TestAddCustomSkill:
    """Test POST /api/skills/custom endpoint"""

    def test_add_new_custom_skill(self, client, db_session):
        """Test adding a new custom skill"""
        response = client.post(
            "/api/skills/custom",
            json={"skill": "GraphQL"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["skill"] == "GraphQL"
        assert data["created"] is True
        assert data["usage_count"] == 1

        # Verify in database
        skill = db_session.query(CustomSkill).filter(
            CustomSkill.skill == "GraphQL"
        ).first()
        assert skill is not None

    def test_add_existing_custom_skill_increments_count(self, client, custom_skill, db_session):
        """Test that adding existing skill increments usage count"""
        initial_count = custom_skill.usage_count

        response = client.post(
            "/api/skills/custom",
            json={"skill": "Kubernetes"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["skill"] == "Kubernetes"
        assert data["created"] is False
        assert data["usage_count"] == initial_count + 1

    def test_add_custom_skill_case_insensitive(self, client, custom_skill):
        """Test that skill matching is case insensitive"""
        response = client.post(
            "/api/skills/custom",
            json={"skill": "kubernetes"}  # lowercase
        )

        assert response.status_code == 200
        data = response.json()

        # Should match existing skill and increment
        assert data["created"] is False

    def test_add_custom_skill_trims_whitespace(self, client, db_session):
        """Test that skill names are trimmed"""
        response = client.post(
            "/api/skills/custom",
            json={"skill": "  Terraform  "}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["skill"] == "Terraform"

    def test_add_custom_skill_with_special_chars(self, client):
        """Test adding skills with allowed special characters"""
        # C++ is valid (contains +)
        response = client.post(
            "/api/skills/custom",
            json={"skill": "C++"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["skill"] == "C++"

        # C# is valid
        response = client.post(
            "/api/skills/custom",
            json={"skill": "C#"}
        )

        assert response.status_code == 200

        # .NET is valid
        response = client.post(
            "/api/skills/custom",
            json={"skill": ".NET"}
        )

        assert response.status_code == 200

    def test_add_custom_skill_invalid_chars(self, client):
        """Test that invalid characters are rejected"""
        response = client.post(
            "/api/skills/custom",
            json={"skill": "Python<script>"}
        )

        # Should get validation error
        assert response.status_code == 422

    def test_add_custom_skill_empty(self, client):
        """Test that empty skills are rejected"""
        response = client.post(
            "/api/skills/custom",
            json={"skill": ""}
        )

        assert response.status_code == 422

    def test_add_custom_skill_whitespace_only(self, client):
        """Test that whitespace-only skills are handled"""
        response = client.post(
            "/api/skills/custom",
            json={"skill": "   "}
        )

        # The endpoint handles this by returning an error response
        # instead of raising an exception (see skills.py:133-137)
        # But it returns 200 with error info when caught in try/except
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.json()
            # Check that error is indicated
            assert "error" in data or data.get("created") is False


class TestGetPopularSkillsErrorHandling:
    """Test error handling in GET /api/skills/popular endpoint"""

    @requires_postgres
    def test_get_popular_skills_database_error_returns_empty(self, client, db_session, monkeypatch):
        """Test that database errors are caught and return empty list"""
        from unittest.mock import Mock
        from app.routers import skills

        # Mock the database execute method to raise an exception
        original_execute = db_session.execute

        def mock_execute(*args, **kwargs):
            raise Exception("Database connection failed")

        # Patch the execute method
        monkeypatch.setattr(db_session, "execute", mock_execute)

        response = client.get("/api/skills/popular")

        assert response.status_code == 200
        data = response.json()
        assert data["skills"] == []
        assert data["total"] == 0


class TestAddCustomSkillErrorHandling:
    """Test error handling in POST /api/skills/custom endpoint"""

    def test_add_custom_skill_database_error_returns_error_response(self, client, db_session, monkeypatch):
        """Test database errors are caught gracefully"""
        from unittest.mock import Mock

        # Mock the database commit method to raise an exception
        def mock_commit():
            raise Exception("Database write failed")

        monkeypatch.setattr(db_session, "commit", mock_commit)

        response = client.post(
            "/api/skills/custom",
            json={"skill": "NewSkill"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["created"] is False
        assert data["usage_count"] == 0
