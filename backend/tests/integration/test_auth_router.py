"""
Integration tests for Auth Router - Critical authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.models.user import User


@pytest.fixture
def client(db_session: Session):
    """FastAPI test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestAuthRegistration:
    """Test user registration endpoint"""

    def test_register_new_user(self, client, sample_user_data):
        """Test registering a new user successfully"""
        response = client.post("/auth/register", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_register_duplicate_email(self, client, test_user):
        """Test registering with an already registered email"""
        response = client.post(
            "/auth/register",
            json={"email": test_user.email, "password": "newpassword123"}
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registering with invalid email format"""
        response = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "password123"}
        )

        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test registering with too short password"""
        response = client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "short"}
        )

        assert response.status_code == 422


class TestAuthLogin:
    """Test user login endpoint"""

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, test_user):
        """Test login with incorrect password"""
        response = client.post(
            "/auth/login",
            json={"email": test_user.email, "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"}
        )

        assert response.status_code == 401

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post("/auth/login", json={})

        assert response.status_code == 422


class TestAuthGetCurrentUser:
    """Test get current user endpoint"""

    def test_get_current_user_authenticated(self, client, test_user):
        """Test getting current user with valid token"""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert "hashed_password" not in data  # Should not expose password

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/auth/me")

        assert response.status_code == 403

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401


class TestAuthLogout:
    """Test logout endpoint"""

    def test_logout_authenticated(self, client, test_user):
        """Test logout with valid token"""
        # First login
        login_response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_logout_no_token(self, client):
        """Test logout without token - JWT logout is client-side, so no auth required"""
        response = client.post("/auth/logout")

        assert response.status_code == 200


class TestAuthFlow:
    """Test complete authentication flow"""

    def test_complete_auth_flow(self, client):
        """Test register -> login -> get user -> logout flow"""
        # 1. Register
        register_response = client.post(
            "/auth/register",
            json={"email": "flowtest@example.com", "password": "password123"}
        )
        assert register_response.status_code == 201
        register_token = register_response.json()["access_token"]

        # 2. Get user with registration token
        user_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {register_token}"}
        )
        assert user_response.status_code == 200
        assert user_response.json()["email"] == "flowtest@example.com"

        # 3. Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {register_token}"}
        )
        assert logout_response.status_code == 200

        # 4. Login again
        login_response = client.post(
            "/auth/login",
            json={"email": "flowtest@example.com", "password": "password123"}
        )
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]

        # 5. Verify can access protected endpoint with new token
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {login_token}"}
        )
        assert me_response.status_code == 200
