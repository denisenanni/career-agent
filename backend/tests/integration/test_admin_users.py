"""
Integration tests for Admin Users endpoint
"""
import pytest
from app.models.user import User
from app.utils.auth import get_password_hash


class TestListUsersEndpoint:
    """Test GET /api/admin/users endpoint"""

    def test_list_users_requires_auth(self, client):
        """Test that unauthenticated users cannot access users list"""
        response = client.get("/api/admin/users")
        assert response.status_code in [401, 403]

    def test_list_users_requires_admin(self, authenticated_client):
        """Test that non-admin users cannot access users list"""
        response = authenticated_client.get("/api/admin/users")
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_list_users_returns_all_users(self, admin_client, db_session):
        """Test that admin can list all users"""
        response = admin_client.get("/api/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1  # At least admin user exists

    def test_list_users_returns_correct_fields(self, admin_client, db_session):
        """Test that user response contains expected fields"""
        response = admin_client.get("/api/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) > 0

        user = data["users"][0]
        assert "id" in user
        assert "email" in user
        assert "full_name" in user
        assert "is_active" in user
        assert "is_admin" in user
        assert "created_at" in user
        # Sensitive fields should NOT be present
        assert "hashed_password" not in user
        assert "cv_text" not in user

    def test_list_users_ordered_by_created_at_desc(self, admin_client, db_session):
        """Test that users are ordered by created_at descending (newest first)"""
        # Create additional users
        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User Two"
        )
        user3 = User(
            email="user3@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User Three"
        )
        db_session.add(user2)
        db_session.add(user3)
        db_session.commit()

        response = admin_client.get("/api/admin/users")

        assert response.status_code == 200
        data = response.json()
        users = data["users"]

        # Should have at least 3 users (admin + 2 new)
        assert len(users) >= 3

        # Verify ordering - newest should be first
        for i in range(len(users) - 1):
            assert users[i]["created_at"] >= users[i + 1]["created_at"]

    def test_list_users_total_matches_users_count(self, admin_client, db_session):
        """Test that total count matches actual users returned"""
        response = admin_client.get("/api/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(data["users"])
