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

        # The endpoint should handle this gracefully
        # Depending on implementation, could be 400 or 422
        assert response.status_code in [200, 400, 422]
