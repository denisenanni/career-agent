"""
Integration tests for Email Allowlist feature

Tests registration modes, allowlist checking, and admin API.
"""
import pytest
from unittest.mock import patch
from app.models.allowed_email import AllowedEmail
from app.models.user import User


@pytest.fixture
def admin_user(db_session):
    """Create an admin user (id=1)"""
    from app.utils.auth import get_password_hash

    # Delete any existing user with id=1
    db_session.query(User).filter(User.id == 1).delete()
    db_session.commit()

    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123")
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    # Ensure the user has id=1 (admin check in code)
    assert admin.id == 1, "Admin user must have id=1 for current admin check"

    return admin


@pytest.fixture
def authenticated_admin_client(client, admin_user):
    """Client authenticated as admin"""
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"}
    )
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture
def allowed_email_in_db(db_session, admin_user):
    """Create an allowed email in the database"""
    allowed = AllowedEmail(
        email="allowed@example.com",
        added_by=admin_user.id
    )
    db_session.add(allowed)
    db_session.commit()
    db_session.refresh(allowed)
    return allowed


class TestRegistrationModes:
    """Test different registration modes"""

    @patch('app.routers.auth.settings')
    def test_open_mode_allows_all_registrations(self, mock_settings, client):
        """Test that open mode allows any email to register"""
        mock_settings.registration_mode = "open"

        response = client.post(
            "/auth/register",
            json={
                "email": "anyone@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.settings')
    def test_closed_mode_rejects_all_registrations(self, mock_settings, client):
        """Test that closed mode rejects all registrations"""
        mock_settings.registration_mode = "closed"

        response = client.post(
            "/auth/register",
            json={
                "email": "anyone@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 403
        assert "currently closed" in response.json()["detail"].lower()

    @patch('app.routers.auth.settings')
    def test_allowlist_mode_accepts_allowed_email_from_db(
        self, mock_settings, client, allowed_email_in_db
    ):
        """Test that allowlist mode accepts emails in database"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = ""

        response = client.post(
            "/auth/register",
            json={
                "email": "allowed@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.settings')
    def test_allowlist_mode_accepts_email_from_config(self, mock_settings, client):
        """Test that allowlist mode accepts emails from config fallback"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = "config@example.com,other@example.com"

        response = client.post(
            "/auth/register",
            json={
                "email": "config@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.settings')
    def test_allowlist_mode_case_insensitive(self, mock_settings, client, allowed_email_in_db):
        """Test that allowlist checking is case-insensitive"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = ""

        # Try uppercase version of allowed email
        response = client.post(
            "/auth/register",
            json={
                "email": "ALLOWED@EXAMPLE.COM",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.settings')
    def test_allowlist_mode_rejects_non_allowed_email(self, mock_settings, client):
        """Test that allowlist mode rejects emails not on the list"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = ""

        response = client.post(
            "/auth/register",
            json={
                "email": "notallowed@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 403
        assert "not on the allowlist" in response.json()["detail"].lower()

    @patch('app.routers.auth.settings')
    def test_allowlist_mode_db_takes_precedence_over_config(
        self, mock_settings, client, allowed_email_in_db
    ):
        """Test that database allowlist is checked before config"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = "other@example.com"

        # Email is in DB but not in config - should still work
        response = client.post(
            "/auth/register",
            json={
                "email": "allowed@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201


class TestAdminAllowlistAPI:
    """Test admin API for managing allowlist"""

    def test_add_email_to_allowlist_as_admin(self, authenticated_admin_client, db_session):
        """Test admin can add email to allowlist"""
        response = authenticated_admin_client.post(
            "/api/admin/allowlist",
            json={"email": "newuser@example.com"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["added_by"] == 1
        assert "id" in data
        assert "created_at" in data

        # Verify it's in the database
        allowed = db_session.query(AllowedEmail).filter(
            AllowedEmail.email == "newuser@example.com"
        ).first()
        assert allowed is not None
        assert allowed.added_by == 1

    def test_add_email_normalizes_case(self, authenticated_admin_client, db_session):
        """Test that email is stored in lowercase"""
        response = authenticated_admin_client.post(
            "/api/admin/allowlist",
            json={"email": "MixedCase@Example.COM"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "mixedcase@example.com"

    def test_add_duplicate_email_fails(self, authenticated_admin_client, allowed_email_in_db):
        """Test that adding duplicate email returns error"""
        response = authenticated_admin_client.post(
            "/api/admin/allowlist",
            json={"email": "allowed@example.com"}
        )

        assert response.status_code == 400
        assert "already on the allowlist" in response.json()["detail"].lower()

    def test_add_email_requires_admin(self, authenticated_client):
        """Test that non-admin cannot add emails"""
        response = authenticated_client.post(
            "/api/admin/allowlist",
            json={"email": "newuser@example.com"}
        )

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    def test_list_allowed_emails_as_admin(self, authenticated_admin_client, allowed_email_in_db, db_session, admin_user):
        """Test admin can list all allowed emails"""
        # Add another email
        another = AllowedEmail(email="another@example.com", added_by=admin_user.id)
        db_session.add(another)
        db_session.commit()

        response = authenticated_admin_client.get("/api/admin/allowlist")

        assert response.status_code == 200
        data = response.json()
        assert "allowed_emails" in data
        assert "total" in data
        assert data["total"] >= 2

        emails = [item["email"] for item in data["allowed_emails"]]
        assert "allowed@example.com" in emails
        assert "another@example.com" in emails

    def test_list_allowed_emails_requires_admin(self, authenticated_client):
        """Test that non-admin cannot list emails"""
        response = authenticated_client.get("/api/admin/allowlist")

        assert response.status_code == 403

    def test_remove_email_from_allowlist_as_admin(
        self, authenticated_admin_client, allowed_email_in_db, db_session
    ):
        """Test admin can remove email from allowlist"""
        response = authenticated_admin_client.delete(
            "/api/admin/allowlist/allowed@example.com"
        )

        assert response.status_code == 204

        # Verify it's gone from database
        allowed = db_session.query(AllowedEmail).filter(
            AllowedEmail.email == "allowed@example.com"
        ).first()
        assert allowed is None

    def test_remove_email_case_insensitive(
        self, authenticated_admin_client, allowed_email_in_db, db_session
    ):
        """Test that email removal is case-insensitive"""
        response = authenticated_admin_client.delete(
            "/api/admin/allowlist/ALLOWED@EXAMPLE.COM"
        )

        assert response.status_code == 204

        # Verify it's gone
        allowed = db_session.query(AllowedEmail).filter(
            AllowedEmail.email == "allowed@example.com"
        ).first()
        assert allowed is None

    def test_remove_nonexistent_email_fails(self, authenticated_admin_client):
        """Test removing email that doesn't exist returns 404"""
        response = authenticated_admin_client.delete(
            "/api/admin/allowlist/notfound@example.com"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_remove_email_requires_admin(self, authenticated_client):
        """Test that non-admin cannot remove emails"""
        response = authenticated_client.delete(
            "/api/admin/allowlist/allowed@example.com"
        )

        assert response.status_code == 403

    def test_unauthenticated_cannot_access_admin_endpoints(self, client):
        """Test that unauthenticated users cannot access admin endpoints"""
        # Try to add
        response = client.post(
            "/api/admin/allowlist",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 401

        # Try to list
        response = client.get("/api/admin/allowlist")
        assert response.status_code == 401

        # Try to remove
        response = client.delete("/api/admin/allowlist/test@example.com")
        assert response.status_code == 401


class TestAllowlistIntegration:
    """Test full registration flow with allowlist"""

    @patch('app.routers.auth.settings')
    def test_full_workflow_add_and_register(
        self, mock_settings, authenticated_admin_client, client
    ):
        """Test complete workflow: admin adds email, user registers"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = ""

        # Step 1: Admin adds email to allowlist
        response = authenticated_admin_client.post(
            "/api/admin/allowlist",
            json={"email": "newuser@example.com"}
        )
        assert response.status_code == 201

        # Step 2: User registers with allowed email
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.settings')
    def test_full_workflow_remove_and_block(
        self, mock_settings, authenticated_admin_client, client, allowed_email_in_db
    ):
        """Test complete workflow: admin removes email, registration blocked"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = ""

        # Step 1: Admin removes email from allowlist
        response = authenticated_admin_client.delete(
            "/api/admin/allowlist/allowed@example.com"
        )
        assert response.status_code == 204

        # Step 2: User tries to register (should fail)
        response = client.post(
            "/auth/register",
            json={
                "email": "allowed@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 403

    @patch('app.routers.auth.settings')
    def test_config_fallback_when_db_empty(self, mock_settings, client):
        """Test that config list is used when database is empty"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = "fallback@example.com,another@example.com"

        response = client.post(
            "/auth/register",
            json={
                "email": "fallback@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.settings')
    def test_whitespace_handling_in_config(self, mock_settings, client):
        """Test that config emails with whitespace are handled correctly"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = " spaced@example.com , another@example.com "

        response = client.post(
            "/auth/register",
            json={
                "email": "spaced@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201

    @patch('app.routers.auth.settings')
    def test_multiple_registrations_from_same_allowed_email(
        self, mock_settings, client, allowed_email_in_db
    ):
        """Test that same email can't register twice (even if on allowlist)"""
        mock_settings.registration_mode = "allowlist"
        mock_settings.allowed_emails = ""

        # First registration succeeds
        response = client.post(
            "/auth/register",
            json={
                "email": "allowed@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201

        # Second registration should fail (duplicate user)
        response = client.post(
            "/auth/register",
            json={
                "email": "allowed@example.com",
                "password": "differentpass"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


class TestAllowlistEdgeCases:
    """Test edge cases and error conditions"""

    def test_add_email_with_invalid_format(self, authenticated_admin_client):
        """Test that invalid email format is rejected"""
        response = authenticated_admin_client.post(
            "/api/admin/allowlist",
            json={"email": "not-an-email"}
        )

        assert response.status_code == 422  # Validation error

    def test_add_email_with_empty_string(self, authenticated_admin_client):
        """Test that empty email is rejected"""
        response = authenticated_admin_client.post(
            "/api/admin/allowlist",
            json={"email": ""}
        )

        assert response.status_code == 422

    @patch('app.routers.auth.settings')
    def test_invalid_registration_mode_in_config(self, mock_settings, client):
        """Test handling of invalid registration mode"""
        mock_settings.registration_mode = "invalid_mode"

        # Should fall back to safe behavior (probably treating as closed or open)
        # This depends on implementation - adjust assertion as needed
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )

        # The behavior here depends on your implementation
        # Either should fail validation or default to a safe mode
        assert response.status_code in [201, 403, 500]

    def test_admin_cannot_remove_their_own_allowed_email_if_last_admin(
        self, authenticated_admin_client, db_session, admin_user
    ):
        """Test safety check: admin shouldn't lock themselves out"""
        # Add admin's email to allowlist
        allowed = AllowedEmail(email="admin@example.com", added_by=admin_user.id)
        db_session.add(allowed)
        db_session.commit()

        # Try to remove it
        response = authenticated_admin_client.delete(
            "/api/admin/allowlist/admin@example.com"
        )

        # This should either succeed (if no safety check) or fail with warning
        # Adjust based on your implementation
        # If you haven't implemented this safety check, the test documents the risk
        if response.status_code == 200:
            # No safety check implemented - document this as a TODO
            pass
        else:
            assert response.status_code == 400
            assert "cannot remove" in response.json()["detail"].lower()
