"""
Integration tests for CV Upload and Parsing Flow

Tests the complete flow from uploading a CV to retrieving parsed data.
"""
import pytest
import io
from unittest.mock import patch


@pytest.fixture
def mock_llm_parse():
    """Mock the LLM parsing service"""
    with patch('app.routers.profile.parse_cv_with_llm') as mock:
        mock.return_value = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0100",
            "summary": "Experienced Software Engineer with 5 years of expertise.",
            "skills": ["Python", "JavaScript", "SQL", "Django", "React"],
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Company Inc.",
                    "start_date": "2020-01",
                    "end_date": "present",
                    "description": "Led development of microservices"
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of Technology",
                    "field": "Computer Science",
                    "end_date": "2018"
                }
            ],
            "years_of_experience": 5
        }
        yield mock


class TestCVUploadFlow:
    """Test complete CV upload and parsing flow"""

    def test_upload_cv_pdf(self, authenticated_client, sample_cv_text, mock_llm_parse):
        """Test uploading a PDF CV"""
        # Create a fake PDF file
        pdf_content = b"%PDF-1.4\n%Test CV content"

        # Patch at the point of use in the router, not where it's defined
        with patch('app.routers.profile.extract_cv_text', return_value=sample_cv_text):
            response = authenticated_client.post(
                "/api/profile/cv",
                files={"file": ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["filename"] == "resume.pdf"
        assert data["file_size"] == len(pdf_content)
        assert data["cv_text_length"] > 0
        assert "Parsed with Claude Haiku" in data["message"]

    def test_upload_cv_text(self, authenticated_client, sample_cv_text, mock_llm_parse):
        """Test uploading a text CV"""
        txt_content = sample_cv_text.encode('utf-8')

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filename"] == "resume.txt"
        assert data["cv_text_length"] > 0

    def test_upload_cv_updates_user_profile(self, authenticated_client, test_user, sample_cv_text, mock_llm_parse, db_session):
        """Test that CV upload updates user profile with parsed data"""
        txt_content = sample_cv_text.encode('utf-8')

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")}
        )

        assert response.status_code == 200

        # Refresh user from database
        db_session.refresh(test_user)

        # User profile should be updated with parsed data
        assert test_user.cv_text is not None
        assert test_user.cv_filename == "resume.txt"
        assert test_user.cv_uploaded_at is not None

        # Parsed data should be in preferences
        assert "parsed_cv" in test_user.preferences
        assert test_user.preferences["parsed_cv"]["name"] == "John Doe"
        assert "Python" in test_user.preferences["parsed_cv"]["skills"]

        # Skills should be synced to main profile
        assert "Python" in test_user.skills
        assert "JavaScript" in test_user.skills

        # Experience years should be synced
        assert test_user.experience_years == 5

    def test_get_parsed_cv(self, authenticated_client, test_user, sample_cv_text, mock_llm_parse, db_session):
        """Test retrieving parsed CV data"""
        # First upload a CV
        txt_content = sample_cv_text.encode('utf-8')
        authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")}
        )

        # Then get the parsed data
        response = authenticated_client.get("/api/profile/cv/parsed")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["phone"] == "+1-555-0100"
        assert len(data["skills"]) == 5
        assert len(data["experience"]) == 1
        assert len(data["education"]) == 1
        assert data["years_of_experience"] == 5

    def test_get_parsed_cv_not_uploaded(self, authenticated_client):
        """Test getting parsed CV when none has been uploaded"""
        response = authenticated_client.get("/api/profile/cv/parsed")

        assert response.status_code == 404
        assert "No parsed CV data found" in response.json()["detail"]

    def test_upload_cv_validates_file_size(self, authenticated_client):
        """Test that large files are rejected"""
        # Create a file larger than 5MB
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("large_resume.txt", io.BytesIO(large_content), "text/plain")}
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_upload_cv_validates_file_type(self, authenticated_client):
        """Test that invalid file types are rejected"""
        # Try to upload an image file
        image_content = b"\x89PNG\r\n\x1a\n"  # PNG header

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("photo.png", io.BytesIO(image_content), "image/png")}
        )

        assert response.status_code == 400
        assert "file format" in response.json()["detail"].lower()

    def test_upload_cv_validates_content_length(self, authenticated_client):
        """Test that CVs with too little content are rejected"""
        # Very short content
        short_content = b"Hi"

        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("short.txt", io.BytesIO(short_content), "text/plain")}
        )

        assert response.status_code == 400
        assert "too short" in response.json()["detail"].lower()

    def test_upload_cv_multiple_times(self, authenticated_client, test_user, sample_cv_text, mock_llm_parse, db_session):
        """Test uploading CV multiple times updates the data"""
        txt_content = sample_cv_text.encode('utf-8')

        # First upload
        response1 = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume_v1.txt", io.BytesIO(txt_content), "text/plain")}
        )
        assert response1.status_code == 200

        db_session.refresh(test_user)
        first_upload_time = test_user.cv_uploaded_at
        assert test_user.cv_filename == "resume_v1.txt"

        # Second upload with different filename
        response2 = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume_v2.txt", io.BytesIO(txt_content), "text/plain")}
        )
        assert response2.status_code == 200

        db_session.refresh(test_user)
        second_upload_time = test_user.cv_uploaded_at

        # Filename should be updated
        assert test_user.cv_filename == "resume_v2.txt"

        # Upload time should be newer
        assert second_upload_time > first_upload_time

    def test_upload_cv_preserves_other_preferences(self, authenticated_client, test_user, sample_cv_text, mock_llm_parse, db_session):
        """Test that uploading CV preserves other preference data"""
        # Set some preferences first
        test_user.preferences = {
            "job_preferences": {
                "min_salary": 120000,
                "work_type": "remote"
            }
        }
        db_session.commit()

        # Upload CV
        txt_content = sample_cv_text.encode('utf-8')
        response = authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")}
        )

        assert response.status_code == 200

        db_session.refresh(test_user)

        # Both preferences should exist
        assert "parsed_cv" in test_user.preferences
        assert "job_preferences" in test_user.preferences
        assert test_user.preferences["job_preferences"]["min_salary"] == 120000

    def test_update_parsed_cv_after_upload(self, authenticated_client, test_user, sample_cv_text, mock_llm_parse, db_session):
        """Test updating parsed CV data after initial upload"""
        # Upload CV
        txt_content = sample_cv_text.encode('utf-8')
        authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")}
        )

        # Update parsed CV
        response = authenticated_client.put(
            "/api/profile/cv/parsed",
            json={
                "name": "Jane Doe",
                "skills": ["Python", "Go", "Kubernetes"]
            }
        )

        assert response.status_code == 200

        db_session.refresh(test_user)

        # Updated fields should reflect changes
        assert test_user.preferences["parsed_cv"]["name"] == "Jane Doe"
        assert "Go" in test_user.preferences["parsed_cv"]["skills"]
        assert "Kubernetes" in test_user.preferences["parsed_cv"]["skills"]

        # Profile should be synced
        assert test_user.full_name == "Jane Doe"
        assert "Go" in test_user.skills

    def test_llm_parsing_failure_still_saves_cv(self, authenticated_client, test_user, sample_cv_text, db_session):
        """Test that CV is still saved even if LLM parsing fails"""
        txt_content = sample_cv_text.encode('utf-8')

        # Mock LLM to return None (parsing failure)
        with patch('app.routers.profile.parse_cv_with_llm', return_value=None):
            response = authenticated_client.post(
                "/api/profile/cv",
                files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "LLM parsing unavailable" in data["message"]

        db_session.refresh(test_user)

        # CV text should still be saved
        assert test_user.cv_text is not None
        assert test_user.cv_filename == "resume.txt"

        # But parsed_cv won't be in preferences
        assert test_user.preferences is None or "parsed_cv" not in test_user.preferences

    def test_profile_endpoint_shows_cv_upload_status(self, authenticated_client, test_user, sample_cv_text, mock_llm_parse):
        """Test that profile endpoint shows CV upload status"""
        # Upload CV
        txt_content = sample_cv_text.encode('utf-8')
        authenticated_client.post(
            "/api/profile/cv",
            files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")}
        )

        # Get profile
        response = authenticated_client.get("/api/profile")

        assert response.status_code == 200
        data = response.json()

        assert data["cv_filename"] == "resume.txt"
        assert data["cv_uploaded_at"] is not None
        assert "Python" in data["skills"]
        assert data["experience_years"] == 5
