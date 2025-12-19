"""
Integration tests for Match Status Updates

Tests the status progression flow and optimistic update compatibility.
"""
import pytest
from app.models.match import Match
from app.models.job import Job
from app.models.user import User


@pytest.fixture
def test_match(db_session, test_user, existing_job):
    """Create a test match"""
    match = Match(
        user_id=test_user.id,
        job_id=existing_job.id,
        score=85.0,
        status="matched",
        analysis="Great match for your skills",
        reasoning={
            "skill_score": 90,
            "location_score": 85,
            "salary_score": 80,
            "experience_score": 85,
            "matching_skills": ["Python", "Django", "PostgreSQL"],
            "missing_skills": ["AWS"],
            "weights": {
                "skills": 0.4,
                "location": 0.1,
                "salary": 0.1,
                "experience": 0.2,
            },
        },
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


class TestMatchStatusUpdates:
    """Test match status update functionality"""

    def test_update_status_to_interested(self, authenticated_client, test_match):
        """Test updating match status to interested"""
        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "interested"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["match_id"] == test_match.id
        assert data["status"] == "interested"

    def test_update_status_to_applied(self, authenticated_client, test_match):
        """Test updating match status to applied"""
        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "applied"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["match_id"] == test_match.id
        assert data["status"] == "applied"

    def test_update_status_to_hidden(self, authenticated_client, test_match):
        """Test hiding a match"""
        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "hidden"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["match_id"] == test_match.id
        assert data["status"] == "hidden"

    def test_update_status_invalid_status(self, authenticated_client, test_match):
        """Test updating with invalid status value"""
        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "invalid_status"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid status" in data["detail"]

    def test_update_status_nonexistent_match(self, authenticated_client):
        """Test updating status for non-existent match"""
        response = authenticated_client.put(
            "/api/matches/99999/status",
            json={"status": "interested"}
        )

        assert response.status_code == 404
        assert "Match not found" in response.json()["detail"]

    def test_update_status_sets_applied_at(self, authenticated_client, test_match, db_session):
        """Test that applied_at is set when status changes to applied"""
        # Initially applied_at should be None
        assert test_match.applied_at is None

        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "applied"}
        )

        assert response.status_code == 200

        # Refresh match from database
        db_session.refresh(test_match)
        assert test_match.applied_at is not None
        assert test_match.status == "applied"

    def test_status_progression_matched_to_interested(self, authenticated_client, test_match, db_session):
        """Test status can progress from matched to interested"""
        assert test_match.status == "matched"

        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "interested"}
        )

        assert response.status_code == 200

        db_session.refresh(test_match)
        assert test_match.status == "interested"

    def test_status_progression_interested_to_applied(self, authenticated_client, test_match, db_session):
        """Test status can progress from interested to applied"""
        # Set initial status to interested
        test_match.status = "interested"
        db_session.commit()

        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "applied"}
        )

        assert response.status_code == 200

        db_session.refresh(test_match)
        assert test_match.status == "applied"

    def test_status_skip_directly_to_applied(self, authenticated_client, test_match, db_session):
        """Test status can skip from matched directly to applied"""
        assert test_match.status == "matched"

        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "applied"}
        )

        assert response.status_code == 200

        db_session.refresh(test_match)
        assert test_match.status == "applied"
        assert test_match.applied_at is not None

    def test_multiple_status_updates(self, authenticated_client, test_match, db_session):
        """Test multiple consecutive status updates"""
        # matched -> interested
        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "interested"}
        )
        assert response.status_code == 200

        # interested -> applied
        response = authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "applied"}
        )
        assert response.status_code == 200

        db_session.refresh(test_match)
        assert test_match.status == "applied"

    def test_list_matches_by_status(self, authenticated_client, test_match, db_session):
        """Test filtering matches by status"""
        # Create additional matches with different statuses
        user = db_session.query(User).filter(User.id == test_match.user_id).first()
        job = db_session.query(Job).filter(Job.id == test_match.job_id).first()

        match2 = Match(
            user_id=user.id,
            job_id=job.id,
            score=75.0,
            status="interested",
            analysis="Another match",
            reasoning={},
        )
        match3 = Match(
            user_id=user.id,
            job_id=job.id,
            score=65.0,
            status="applied",
            analysis="Third match",
            reasoning={},
        )
        db_session.add(match2)
        db_session.add(match3)
        db_session.commit()

        # Test filtering by status
        response = authenticated_client.get("/api/matches?status=matched")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["matches"][0]["status"] == "matched"

        response = authenticated_client.get("/api/matches?status=interested")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["matches"][0]["status"] == "interested"

        response = authenticated_client.get("/api/matches?status=applied")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["matches"][0]["status"] == "applied"

    def test_match_visibility_after_status_change(self, authenticated_client, test_match):
        """Test that match is still visible after status change"""
        # Get initial matches count
        response = authenticated_client.get("/api/matches")
        initial_count = response.json()["total"]
        assert initial_count >= 1

        # Update status to interested
        authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "interested"}
        )

        # Match should still be visible
        response = authenticated_client.get("/api/matches")
        assert response.json()["total"] == initial_count

        # Update status to applied
        authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "applied"}
        )

        # Match should still be visible
        response = authenticated_client.get("/api/matches")
        assert response.json()["total"] == initial_count

    def test_hidden_match_not_in_default_list(self, authenticated_client, test_match):
        """Test that hidden matches don't appear in default list"""
        # Hide the match
        authenticated_client.put(
            f"/api/matches/{test_match.id}/status",
            json={"status": "hidden"}
        )

        # Get matches without status filter
        response = authenticated_client.get("/api/matches")
        matches = response.json()["matches"]

        # Hidden match should not appear
        hidden_match_ids = [m["id"] for m in matches if m["id"] == test_match.id]
        assert len(hidden_match_ids) == 0

        # But it should appear when filtering by hidden status
        response = authenticated_client.get("/api/matches?status=hidden")
        matches = response.json()["matches"]
        hidden_match_ids = [m["id"] for m in matches if m["id"] == test_match.id]
        assert len(hidden_match_ids) == 1
