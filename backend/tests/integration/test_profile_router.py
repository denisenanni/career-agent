"""
Integration tests for Profile Router
"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


class TestProfileEndpoints:
    """Test profile management endpoints"""

    def test_get_profile(self, client):
        """Test GET /api/profile endpoint"""
        response = client.get("/api/profile")

        assert response.status_code == 200
        data = response.json()

        # Currently returns not implemented
        assert "error" in data
        assert data["error"] == "Not implemented"

    def test_update_profile(self, client):
        """Test PUT /api/profile endpoint"""
        profile_data = {
            "skills": ["Python", "Django", "PostgreSQL"],
            "experience_years": 5,
            "preferences": {"remote_only": True, "min_salary": 100000},
        }

        response = client.put("/api/profile", json=profile_data)

        assert response.status_code == 200
        data = response.json()

        # Currently returns not implemented
        assert "error" in data
        assert data["error"] == "Not implemented"

    def test_update_profile_partial(self, client):
        """Test updating profile with partial data"""
        # Only update skills
        response = client.put("/api/profile", json={"skills": ["Python"]})

        assert response.status_code == 200

    def test_upload_cv(self, client):
        """Test POST /api/profile/cv endpoint"""
        # Create a fake PDF file
        pdf_content = b"%PDF-1.4 fake pdf content"
        file_data = BytesIO(pdf_content)

        response = client.post(
            "/api/profile/cv",
            files={"file": ("resume.pdf", file_data, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filename"] == "resume.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["status"] == "uploaded"
        assert "not yet implemented" in data["message"].lower()

    def test_upload_cv_docx(self, client):
        """Test uploading a DOCX file"""
        docx_content = b"fake docx content"
        file_data = BytesIO(docx_content)

        response = client.post(
            "/api/profile/cv",
            files={"file": ("resume.docx", file_data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filename"] == "resume.docx"
        assert "openxmlformats" in data["content_type"]

    def test_upload_cv_without_file(self, client):
        """Test uploading CV without providing a file"""
        response = client.post("/api/profile/cv")

        # Should return 422 validation error
        assert response.status_code == 422
