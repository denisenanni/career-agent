"""
Integration tests for Profile Router - CV upload and parsing
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from io import BytesIO

from app.main import app
from app.database import get_db


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


@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authentication token"""
    # Login to get token
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    token = response.json()["access_token"]

    # Add token to client headers
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


class TestProfileEndpoints:
    """Test profile management endpoints"""

    def test_get_profile_authenticated(self, authenticated_client, test_user):
        """Test GET /api/profile with authentication"""
        response = authenticated_client.get("/api/profile")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert "skills" in data
        assert "experience_years" in data

    def test_get_profile_unauthenticated(self, client):
        """Test GET /api/profile without authentication"""
        response = client.get("/api/profile")

        assert response.status_code == 403

    def test_update_profile(self, authenticated_client, test_user):
        """Test PUT /api/profile"""
        profile_data = {
            "full_name": "John Doe",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience_years": 5,
            "bio": "Experienced software engineer"
        }

        response = authenticated_client.put("/api/profile", json=profile_data)

        assert response.status_code == 200
        data = response.json()

        assert data["full_name"] == "John Doe"
        assert "Python" in data["skills"]
        assert data["experience_years"] == 5
        assert data["bio"] == "Experienced software engineer"

    def test_update_profile_partial(self, authenticated_client):
        """Test updating profile with partial data"""
        response = authenticated_client.put(
            "/api/profile",
            json={"skills": ["Python", "Django"]}
        )

        assert response.status_code == 200
        data = response.json()

        assert "Python" in data["skills"]
        assert "Django" in data["skills"]


class TestCVUpload:
    """Test CV upload and parsing endpoints"""

    def test_upload_cv_txt_success(self, authenticated_client, sample_cv_text):
        """Test uploading a TXT CV successfully"""
        cv_file = BytesIO(sample_cv_text.encode('utf-8'))

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", cv_file, "text/plain")}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filename"] == "resume.txt"
        assert data["content_type"] == "text/plain"
        assert data["cv_text_length"] > 0
        assert "uploaded_at" in data
        assert "message" in data
        # Should mention Claude Haiku parsing if API key is configured
        assert "uploaded successfully" in data["message"].lower()

    def test_upload_cv_pdf(self, authenticated_client, sample_cv_text):
        """Test uploading a PDF CV"""
        # Mock PDF extraction since creating a valid PDF is complex
        from unittest.mock import patch

        # Use sample_cv_text as the mock extracted text
        with patch('app.routers.profile.extract_cv_text', return_value=sample_cv_text):
            pdf_content = b"%PDF-1.4\n%mock pdf content"
            cv_file = BytesIO(pdf_content)

            response = authenticated_client.post(
                "/api/profile/cv",
                files={"file": ("resume.pdf", cv_file, "application/pdf")}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "resume.pdf"
            assert "cv_text_length" in data

    def test_upload_cv_invalid_type(self, authenticated_client):
        """Test uploading invalid file type"""
        file_data = BytesIO(b"some content")

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("file.exe", file_data, "application/exe")}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_upload_cv_too_large(self, authenticated_client):
        """Test uploading file that's too large (>5MB)"""
        # Create 6MB file
        large_content = b"x" * (6 * 1024 * 1024)
        file_data = BytesIO(large_content)

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("large.txt", file_data, "text/plain")}
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_upload_cv_empty_content(self, authenticated_client):
        """Test uploading CV with insufficient content"""
        # Very short content (less than 50 chars)
        short_content = b"short"
        file_data = BytesIO(short_content)

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("short.txt", file_data, "text/plain")}
        )

        assert response.status_code == 400
        assert "too short" in response.json()["detail"].lower()

    def test_upload_cv_unauthenticated(self, client, sample_cv_text):
        """Test uploading CV without authentication"""
        cv_file = BytesIO(sample_cv_text.encode('utf-8'))

        response = client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", cv_file, "text/plain")}
        )

        assert response.status_code == 403

    def test_get_parsed_cv(self, authenticated_client, sample_cv_text):
        """Test GET /api/profile/cv/parsed after upload"""
        # First upload a CV
        cv_file = BytesIO(sample_cv_text.encode('utf-8'))
        upload_response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", cv_file, "text/plain")}
        )
        assert upload_response.status_code == 200

        # Then get parsed CV
        response = authenticated_client.get("/api/profile/cv/parsed")

        # If LLM parsing is enabled (API key configured), should return parsed data
        # Otherwise returns 404
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "skills" in data
            assert "experience" in data
            assert isinstance(data["skills"], list)
            assert isinstance(data["experience"], list)
        else:
            assert response.status_code == 404

    def test_get_parsed_cv_no_upload(self, authenticated_client):
        """Test getting parsed CV when no CV has been uploaded"""
        response = authenticated_client.get("/api/profile/cv/parsed")

        assert response.status_code == 404
        assert "no cv" in response.json()["detail"].lower() or "no parsed" in response.json()["detail"].lower()


class TestProfileFlow:
    """Test complete profile management flow"""

    def test_complete_profile_flow(self, authenticated_client, sample_cv_text):
        """Test complete flow: update profile -> upload CV -> verify data"""
        # 1. Update profile
        profile_update = authenticated_client.put(
            "/api/profile",
            json={
                "full_name": "Jane Smith",
                "bio": "Software developer",
                "skills": ["Python"]
            }
        )
        assert profile_update.status_code == 200

        # 2. Upload CV
        cv_file = BytesIO(sample_cv_text.encode('utf-8'))
        cv_upload = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("cv.txt", cv_file, "text/plain")}
        )
        assert cv_upload.status_code == 200

        # 3. Verify profile includes CV data
        profile_get = authenticated_client.get("/api/profile")
        assert profile_get.status_code == 200
        data = profile_get.json()

        assert data["cv_filename"] == "cv.txt"
        assert data["cv_uploaded_at"] is not None
        # Skills should be merged from manual update and CV parsing
        assert "Python" in data["skills"]
