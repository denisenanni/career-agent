"""
Integration tests for Matches Router
"""
import pytest


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

    def test_generate_application(self, authenticated_client):
        """Test POST /api/matches/{job_id}/generate endpoint"""
        job_id = "123"

        response = authenticated_client.post(f"/api/matches/{job_id}/generate")

        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == job_id
        assert data["cover_letter"] is None
        assert data["cv_highlights"] is None
        assert data["status"] == "not_implemented"

    def test_generate_application_different_job_ids(self, authenticated_client):
        """Test generating applications for different job IDs"""
        job_ids = ["456", "789", "abc123"]

        for job_id in job_ids:
            response = authenticated_client.post(f"/api/matches/{job_id}/generate")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id

    def test_update_match_status(self, authenticated_client):
        """Test PUT /api/matches/{job_id}/status endpoint"""
        job_id = "123"
        new_status = "applied"

        response = authenticated_client.put(f"/api/matches/{job_id}/status?status={new_status}")

        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == job_id
        assert data["status"] == new_status

    def test_update_match_status_all_statuses(self, authenticated_client):
        """Test updating match status with different status values"""
        job_id = "123"
        statuses = ["interested", "applied", "rejected", "hidden"]

        for status in statuses:
            response = authenticated_client.put(f"/api/matches/{job_id}/status?status={status}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == status

    def test_update_match_status_different_job_ids(self, authenticated_client):
        """Test updating status for different job IDs"""
        job_ids = ["123", "456", "789"]

        for job_id in job_ids:
            response = authenticated_client.put(f"/api/matches/{job_id}/status?status=interested")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id
