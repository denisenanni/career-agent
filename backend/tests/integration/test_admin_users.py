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


class TestUpdateUserEndpoint:
    """Test PUT /api/admin/users/{user_id} endpoint"""

    def test_update_user_requires_auth(self, client, db_session):
        """Test that unauthenticated users cannot update users"""
        # Create a test user
        user = User(
            email="target@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Target User"
        )
        db_session.add(user)
        db_session.commit()

        response = client.put(f"/api/admin/users/{user.id}", json={"is_active": False})
        assert response.status_code in [401, 403]

    def test_update_user_requires_admin(self, authenticated_client, db_session):
        """Test that non-admin users cannot update users"""
        # Create a test user
        user = User(
            email="target2@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Target User 2"
        )
        db_session.add(user)
        db_session.commit()

        response = authenticated_client.put(f"/api/admin/users/{user.id}", json={"is_active": False})
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_update_user_is_active(self, admin_client, db_session):
        """Test that admin can deactivate a user"""
        # Create a test user
        user = User(
            email="target3@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Target User 3",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        response = admin_client.put(f"/api/admin/users/{user.id}", json={"is_active": False})

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

        # Verify in database
        db_session.refresh(user)
        assert user.is_active is False

    def test_update_user_is_admin(self, admin_client, db_session):
        """Test that admin can grant admin privileges to a user"""
        # Create a test user
        user = User(
            email="target4@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Target User 4",
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()

        response = admin_client.put(f"/api/admin/users/{user.id}", json={"is_admin": True})

        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is True

        # Verify in database
        db_session.refresh(user)
        assert user.is_admin is True

    def test_update_user_not_found(self, admin_client):
        """Test that updating non-existent user returns 404"""
        response = admin_client.put("/api/admin/users/99999", json={"is_active": False})
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_admin_cannot_update_self(self, admin_client, db_session):
        """Test that admin cannot modify their own account via admin endpoint"""
        # Get the admin user (email is admin@example.com based on the fixture)
        admin_user = db_session.query(User).filter(User.email == "admin@example.com").first()
        assert admin_user is not None

        response = admin_client.put(f"/api/admin/users/{admin_user.id}", json={"is_active": False})
        assert response.status_code == 400
        assert "Cannot modify your own account" in response.json()["detail"]

    def test_update_user_cache_invalidation(self, admin_client, db_session):
        """Test that user cache is invalidated after admin update"""
        from app.dependencies.auth import _get_cached_user, _cache_user

        # Create and cache a user
        user = User(
            email="target5@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Target User 5",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Cache the user
        _cache_user(user)

        # Verify user is cached
        cached = _get_cached_user(user.id)
        assert cached is not None
        assert cached.is_active is True

        # Update user via admin endpoint
        response = admin_client.put(f"/api/admin/users/{user.id}", json={"is_active": False})
        assert response.status_code == 200

        # Cache should be invalidated
        cached_after = _get_cached_user(user.id)
        assert cached_after is None
