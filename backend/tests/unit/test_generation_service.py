"""
Unit tests for generation service
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from app.services.generation import (
    generate_cover_letter,
    generate_cv_highlights,
)


@pytest.fixture
def mock_user():
    """Create a mock user object"""
    user = MagicMock()
    user.id = 1
    user.full_name = "John Doe"
    user.skills = ["Python", "FastAPI", "React"]
    user.experience_years = 5
    user.preferences = {
        "parsed_cv": {
            "name": "John Doe",
            "summary": "Senior Software Engineer with 5 years of experience",
            "years_of_experience": 5,
            "experience": [
                {
                    "title": "Senior Developer",
                    "company": "Tech Corp",
                    "start_date": "2020-01",
                    "end_date": "present",
                    "description": "Led development of microservices architecture"
                },
                {
                    "title": "Software Engineer",
                    "company": "Startup Inc",
                    "start_date": "2018-01",
                    "end_date": "2019-12",
                    "description": "Built REST APIs and React frontend"
                }
            ]
        }
    }
    return user


@pytest.fixture
def mock_job():
    """Create a mock job object"""
    job = MagicMock()
    job.id = 100
    job.title = "Senior Backend Engineer"
    job.company = "Great Company"
    job.description = "Looking for a backend engineer with Python experience..."
    return job


@pytest.fixture
def mock_match():
    """Create a mock match object"""
    match = MagicMock()
    match.score = 85.0
    match.reasoning = {
        "job_requirements": {
            "required_skills": ["Python", "FastAPI", "PostgreSQL"]
        },
        "matching_skills": ["Python", "FastAPI"],
        "missing_skills": ["PostgreSQL"]
    }
    return match


class TestGenerateCoverLetter:
    """Test cover letter generation"""

    def test_generate_cover_letter_no_client(self, mock_user, mock_job, mock_match):
        """Test when Anthropic client is not configured"""
        with patch('app.services.generation.client', None):
            result = generate_cover_letter(mock_user, mock_job, mock_match)

            assert result is None

    def test_generate_cover_letter_cache_hit(self, mock_user, mock_job, mock_match):
        """Test when cover letter is in cache"""
        cached_data = {
            "cover_letter": "Dear Hiring Manager, I am excited...",
            "generated_at": "2025-01-01T12:00:00"
        }

        with patch('app.services.generation.client', MagicMock()):
            with patch('app.services.generation.cache_get', return_value=cached_data):
                result = generate_cover_letter(mock_user, mock_job, mock_match)

                assert result is not None
                assert result["cached"] is True
                assert result["cover_letter"] == cached_data["cover_letter"]
                assert result["generated_at"] == cached_data["generated_at"]

    def test_generate_cover_letter_cache_miss(self, mock_user, mock_job, mock_match):
        """Test when cover letter needs to be generated"""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Dear Hiring Manager,\n\nI am writing...")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set') as mock_cache_set:
                    result = generate_cover_letter(mock_user, mock_job, mock_match)

                    assert result is not None
                    assert result["cached"] is False
                    assert "Dear Hiring Manager" in result["cover_letter"]
                    mock_cache_set.assert_called_once()

    def test_generate_cover_letter_api_error(self, mock_user, mock_job, mock_match):
        """Test when API call fails"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                result = generate_cover_letter(mock_user, mock_job, mock_match)

                assert result is None

    def test_generate_cover_letter_no_preferences(self, mock_job, mock_match):
        """Test with user having no preferences"""
        user = MagicMock()
        user.id = 1
        user.full_name = "Jane Doe"
        user.skills = None
        user.experience_years = 0
        user.preferences = None

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Dear Hiring Manager...")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set'):
                    result = generate_cover_letter(user, mock_job, mock_match)

                    assert result is not None
                    assert result["cover_letter"] is not None

    def test_generate_cover_letter_no_match_reasoning(self, mock_user, mock_job):
        """Test with match having no reasoning"""
        match = MagicMock()
        match.score = 75.0
        match.reasoning = None

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Dear Hiring Manager...")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set'):
                    result = generate_cover_letter(mock_user, mock_job, match)

                    assert result is not None


class TestGenerateCvHighlights:
    """Test CV highlights generation"""

    def test_generate_cv_highlights_no_client(self, mock_user, mock_job, mock_match):
        """Test when Anthropic client is not configured"""
        with patch('app.services.generation.client', None):
            result = generate_cv_highlights(mock_user, mock_job, mock_match)

            assert result is None

    def test_generate_cv_highlights_cache_hit(self, mock_user, mock_job, mock_match):
        """Test when highlights are in cache"""
        cached_data = {
            "highlights": ["Led backend team...", "Developed APIs..."],
            "generated_at": "2025-01-01T12:00:00"
        }

        with patch('app.services.generation.client', MagicMock()):
            with patch('app.services.generation.cache_get', return_value=cached_data):
                result = generate_cv_highlights(mock_user, mock_job, mock_match)

                assert result is not None
                assert result["cached"] is True
                assert result["highlights"] == cached_data["highlights"]

    def test_generate_cv_highlights_cache_miss(self, mock_user, mock_job, mock_match):
        """Test when highlights need to be generated"""
        highlights_json = '["Led backend team of 5 engineers", "Developed REST APIs"]'
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=highlights_json)]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set') as mock_cache_set:
                    result = generate_cv_highlights(mock_user, mock_job, mock_match)

                    assert result is not None
                    assert result["cached"] is False
                    assert len(result["highlights"]) == 2
                    mock_cache_set.assert_called_once()

    def test_generate_cv_highlights_with_markdown_code_block(self, mock_user, mock_job, mock_match):
        """Test parsing JSON from markdown code block"""
        highlights_response = '```json\n["Highlight 1", "Highlight 2"]\n```'
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=highlights_response)]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set'):
                    result = generate_cv_highlights(mock_user, mock_job, mock_match)

                    assert result is not None
                    assert len(result["highlights"]) == 2

    def test_generate_cv_highlights_json_parse_error(self, mock_user, mock_job, mock_match):
        """Test handling of invalid JSON response"""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="This is not valid JSON")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                result = generate_cv_highlights(mock_user, mock_job, mock_match)

                assert result is None

    def test_generate_cv_highlights_not_list_response(self, mock_user, mock_job, mock_match):
        """Test when response is valid JSON but not a list"""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"key": "value"}')]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                result = generate_cv_highlights(mock_user, mock_job, mock_match)

                assert result is None

    def test_generate_cv_highlights_api_error(self, mock_user, mock_job, mock_match):
        """Test when API call fails"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                result = generate_cv_highlights(mock_user, mock_job, mock_match)

                assert result is None

    def test_generate_cv_highlights_no_preferences(self, mock_job, mock_match):
        """Test with user having no preferences"""
        user = MagicMock()
        user.id = 1
        user.skills = []
        user.preferences = None

        highlights_json = '["Generic highlight 1", "Generic highlight 2"]'
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=highlights_json)]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set'):
                    result = generate_cv_highlights(user, mock_job, mock_match)

                    assert result is not None
                    assert len(result["highlights"]) == 2

    def test_generate_cv_highlights_no_job_description(self, mock_user, mock_match):
        """Test with job having no description"""
        job = MagicMock()
        job.id = 100
        job.title = "Developer"
        job.description = None

        highlights_json = '["Highlight"]'
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=highlights_json)]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set'):
                    result = generate_cv_highlights(mock_user, job, mock_match)

                    assert result is not None

    def test_generate_cv_highlights_code_block_with_json_prefix(self, mock_user, mock_job, mock_match):
        """Test parsing JSON from code block with 'json' prefix on first line"""
        highlights_response = '```\njson\n["Highlight 1"]\n```'
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=highlights_response)]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch('app.services.generation.client', mock_client):
            with patch('app.services.generation.cache_get', return_value=None):
                with patch('app.services.generation.cache_set'):
                    result = generate_cv_highlights(mock_user, mock_job, mock_match)

                    assert result is not None
                    assert len(result["highlights"]) == 1
