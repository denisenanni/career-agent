"""
Integration tests for Matches Router
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.job import Job
from app.models.match import Match


@pytest.fixture
def sample_job(db_session: Session):
    """Create a sample job in the database"""
    job = Job(
        source="test_source",
        source_id="test_job_for_match",
        url="https://example.com/job/match-test",
        title="Test Developer Position",
        company="Test Company",
        description="A test job for match testing",
        scraped_at=datetime.now(timezone.utc),
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_match(db_session: Session, test_user, sample_job):
    """Create a sample match in the database"""
    match = Match(
        user_id=test_user.id,
        job_id=sample_job.id,
        score=85.0,
        status="matched",
        reasoning={"summary": "Good skill match", "details": ["Python", "FastAPI"]}
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


class TestMatchesEndpoints:
    """Test job matching endpoints"""

    def test_list_matches(self, authenticated_client):
        """Test GET /api/matches endpoint"""
        response = authenticated_client.get("/api/matches")

        assert response.status_code == 200
        data = response.json()

        assert "matches" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["matches"] == []
        assert data["total"] == 0
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_list_matches_with_filters(self, authenticated_client):
        """Test listing matches with filters"""
        response = authenticated_client.get("/api/matches?min_score=80&status=interested&limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_list_matches_with_min_score(self, authenticated_client):
        """Test filtering matches by minimum score"""
        response = authenticated_client.get("/api/matches?min_score=75.5")

        assert response.status_code == 200

    def test_list_matches_with_status(self, authenticated_client):
        """Test filtering matches by status"""
        statuses = ["matched", "interested", "applied", "rejected", "hidden"]

        for status in statuses:
            response = authenticated_client.get(f"/api/matches?status={status}")
            assert response.status_code == 200

    def test_list_matches_pagination(self, authenticated_client):
        """Test pagination parameters"""
        response = authenticated_client.get("/api/matches?limit=25&offset=10")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 25
        assert data["offset"] == 10

    def test_list_matches_with_data(self, authenticated_client, sample_match):
        """Test listing matches when matches exist"""
        response = authenticated_client.get("/api/matches")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["matches"]) == 1
        assert data["matches"][0]["score"] == 85.0
        assert data["matches"][0]["status"] == "matched"

    def test_get_match(self, authenticated_client, sample_match):
        """Test GET /api/matches/{match_id} endpoint"""
        response = authenticated_client.get(f"/api/matches/{sample_match.id}")

        assert response.status_code == 200
        data = response.json()

        # Response structure is {"match": {...}, "job": {...}}
        assert "match" in data
        assert "job" in data
        assert data["match"]["id"] == sample_match.id
        assert data["match"]["score"] == 85.0
        assert data["match"]["status"] == "matched"

    def test_get_match_not_found(self, authenticated_client):
        """Test getting a non-existent match"""
        response = authenticated_client.get("/api/matches/99999")

        assert response.status_code == 404

    def test_update_match_status(self, authenticated_client, sample_match):
        """Test PUT /api/matches/{match_id}/status endpoint"""
        new_status = "applied"

        response = authenticated_client.put(
            f"/api/matches/{sample_match.id}/status",
            json={"status": new_status}
        )

        assert response.status_code == 200
        data = response.json()

        # Response structure is {"match_id": ..., "status": ...}
        assert data["match_id"] == sample_match.id
        assert data["status"] == new_status

    def test_update_match_status_all_statuses(self, authenticated_client, sample_match):
        """Test updating match status with different status values"""
        statuses = ["interested", "applied", "rejected", "hidden"]

        for status in statuses:
            response = authenticated_client.put(
                f"/api/matches/{sample_match.id}/status",
                json={"status": status}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == status

    def test_update_match_status_not_found(self, authenticated_client):
        """Test updating status of non-existent match"""
        response = authenticated_client.put(
            "/api/matches/99999/status",
            json={"status": "interested"}
        )

        assert response.status_code == 404

    def test_update_match_status_invalid_status(self, authenticated_client, sample_match):
        """Test updating match with invalid status value"""
        response = authenticated_client.put(
            f"/api/matches/{sample_match.id}/status",
            json={"status": "invalid_status"}
        )

        # The endpoint should return 400 for invalid status
        assert response.status_code == 400

    def test_list_matches_max_score_filter(self, authenticated_client, sample_match):
        """Test filtering matches by maximum score"""
        response = authenticated_client.get("/api/matches?max_score=90")

        assert response.status_code == 200
        data = response.json()
        # sample_match has score 85, should be included
        assert data["total"] == 1

    def test_list_matches_limit_exceeds_max(self, authenticated_client):
        """Test that limit is capped at 100"""
        response = authenticated_client.get("/api/matches?limit=200")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 100  # Should be capped

    def test_update_match_status_sets_applied_at(self, authenticated_client, sample_match, db_session):
        """Test that updating status to 'applied' sets applied_at timestamp"""
        # Initially applied_at should be None
        assert sample_match.applied_at is None

        response = authenticated_client.put(
            f"/api/matches/{sample_match.id}/status",
            json={"status": "applied"}
        )

        assert response.status_code == 200

        # Refresh the match from database
        db_session.refresh(sample_match)

        # Now applied_at should be set
        assert sample_match.applied_at is not None
        assert sample_match.status == "applied"


class TestGenerationEndpoints:
    """Test content generation endpoints"""

    @pytest.fixture
    def sample_job_with_details(self, db_session):
        """Create a job with full details for generation testing"""
        job = Job(
            source="test_source",
            source_id="test_job_generation",
            url="https://example.com/job/gen-test",
            title="Senior Python Developer",
            company="Tech Company",
            description="Looking for a senior Python developer with FastAPI experience",
            location="San Francisco, CA",
            remote_type="hybrid",
            salary_min=150000,
            salary_max=200000,
            scraped_at=datetime.now(timezone.utc),
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    @pytest.fixture
    def sample_match_for_generation(self, db_session, test_user, sample_job_with_details):
        """Create a match for generation testing"""
        match = Match(
            user_id=test_user.id,
            job_id=sample_job_with_details.id,
            score=90.0,
            status="interested",
            reasoning={
                "summary": "Strong match",
                "job_requirements": {"required_skills": ["Python", "FastAPI"]},
                "matching_skills": ["Python", "FastAPI"],
                "missing_skills": []
            },
            analysis="Strong candidate for this role"
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)
        return match

    def test_generate_cover_letter_match_not_found(self, authenticated_client):
        """Test generating cover letter for non-existent match"""
        response = authenticated_client.post("/api/matches/99999/generate-cover-letter")

        assert response.status_code == 404
        assert "Match not found" in response.json()["detail"]

    def test_generate_highlights_match_not_found(self, authenticated_client):
        """Test generating highlights for non-existent match"""
        response = authenticated_client.post("/api/matches/99999/generate-highlights")

        assert response.status_code == 404
        assert "Match not found" in response.json()["detail"]

    def test_regenerate_match_not_found(self, authenticated_client):
        """Test regenerating content for non-existent match"""
        response = authenticated_client.post("/api/matches/99999/regenerate")

        assert response.status_code == 404
        assert "Match not found" in response.json()["detail"]

    def test_regenerate_clears_cache(self, authenticated_client, sample_match_for_generation):
        """Test that regenerate endpoint clears cache"""
        from unittest.mock import patch

        with patch('app.routers.matches.cache_delete_pattern') as mock_cache_delete:
            mock_cache_delete.return_value = 2

            response = authenticated_client.post(f"/api/matches/{sample_match_for_generation.id}/regenerate")

            assert response.status_code == 200
            data = response.json()
            assert "Cache cleared" in data["message"]
            assert data["keys_invalidated"] == 2

            # Verify cache_delete_pattern was called
            mock_cache_delete.assert_called_once()


class TestRefreshMatches:
    """Test refresh matches endpoint"""

    @pytest.fixture
    def user_with_skills(self, db_session, test_user):
        """Ensure test user has skills"""
        test_user.skills = ["Python", "FastAPI", "React"]
        db_session.commit()
        db_session.refresh(test_user)
        return test_user

    @pytest.fixture
    def some_jobs(self, db_session):
        """Create some jobs for matching"""
        jobs = []
        for i in range(3):
            job = Job(
                source="test_source",
                source_id=f"test_job_refresh_{i}",
                url=f"https://example.com/job/refresh-{i}",
                title=f"Python Developer {i}",
                company=f"Company {i}",
                description="Looking for Python developer with FastAPI experience",
                scraped_at=datetime.now(timezone.utc),
            )
            db_session.add(job)
            jobs.append(job)
        db_session.commit()
        return jobs

    @pytest.mark.asyncio
    async def test_refresh_matches_creates_matches(self, authenticated_client, user_with_skills, some_jobs):
        """Test that refresh matches endpoint creates matches"""
        from unittest.mock import patch, AsyncMock

        # Mock the matching service to return some matches
        with patch('app.routers.matches.match_user_with_all_jobs', new_callable=AsyncMock) as mock_match:
            mock_match.return_value = [{"job_id": 1, "score": 75.0}]

            response = authenticated_client.post("/api/matches/refresh")

            assert response.status_code == 200
            data = response.json()

            assert "matches_created" in data
            assert "matches_updated" in data
            assert "total_jobs_processed" in data

    def test_refresh_matches_error_handling(self, authenticated_client):
        """Test that refresh matches handles errors gracefully"""
        from unittest.mock import patch, AsyncMock

        # Mock the matching service to raise an exception
        with patch('app.routers.matches.match_user_with_all_jobs', new_callable=AsyncMock) as mock_match:
            mock_match.side_effect = Exception("Matching service failed")

            response = authenticated_client.post("/api/matches/refresh")

            assert response.status_code == 500
            assert "Failed to refresh matches" in response.json()["detail"]
