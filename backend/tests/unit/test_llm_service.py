"""
Unit tests for LLM Service - Critical Claude Haiku integration testing
"""
import pytest
import json
from unittest.mock import Mock, patch
from app.services.llm import parse_cv_with_llm, extract_job_requirements


class TestCVParsing:
    """Test CV parsing with Claude Haiku"""

    @pytest.fixture
    def mock_claude_response(self):
        """Mock successful Claude API response for CV parsing"""
        return Mock(
            content=[
                Mock(
                    text=json.dumps({
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1-555-0100",
                        "summary": "Experienced Software Engineer with 5 years of expertise",
                        "skills": ["Python", "JavaScript", "SQL", "Django", "FastAPI"],
                        "experience": [
                            {
                                "company": "Tech Company Inc.",
                                "title": "Senior Software Engineer",
                                "start_date": "2020-01",
                                "end_date": "present",
                                "description": "Led development of microservices"
                            },
                            {
                                "company": "Startup LLC",
                                "title": "Software Engineer",
                                "start_date": "2018-06",
                                "end_date": "2019-12",
                                "description": "Developed RESTful APIs"
                            }
                        ],
                        "education": [
                            {
                                "institution": "University of Technology",
                                "degree": "Bachelor of Science in Computer Science",
                                "field": None,
                                "end_date": "2018"
                            }
                        ],
                        "years_of_experience": 5
                    })
                )
            ]
        )

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_parse_cv_success(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text, mock_claude_response):
        """Test successful CV parsing"""
        mock_client.messages.create.return_value = mock_claude_response

        result = parse_cv_with_llm(sample_cv_text)

        assert result is not None
        assert result["name"] == "John Doe"
        assert result["email"] == "john.doe@example.com"
        assert result["phone"] == "+1-555-0100"
        assert "Python" in result["skills"]
        assert len(result["experience"]) == 2
        assert len(result["education"]) == 1
        assert result["years_of_experience"] == 5

        # Verify Claude was called with correct parameters
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert call_kwargs["temperature"] == 0
        assert sample_cv_text in call_kwargs["messages"][0]["content"]

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_parse_cv_with_markdown_wrapper(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text):
        """Test parsing when Claude returns JSON wrapped in markdown"""
        # Mock response with markdown code block
        mock_response = Mock(
            content=[
                Mock(
                    text='```json\n{"name": "Jane Doe", "email": "jane@example.com", "skills": ["Python"], "experience": [], "education": [], "years_of_experience": 3}\n```'
                )
            ]
        )
        mock_client.messages.create.return_value = mock_response

        result = parse_cv_with_llm(sample_cv_text)

        assert result is not None
        assert result["name"] == "Jane Doe"
        assert result["email"] == "jane@example.com"

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_parse_cv_invalid_json(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text):
        """Test handling of invalid JSON response"""
        mock_response = Mock(
            content=[Mock(text="This is not valid JSON")]
        )
        mock_client.messages.create.return_value = mock_response

        result = parse_cv_with_llm(sample_cv_text)

        assert result is None

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_parse_cv_api_error(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text):
        """Test handling of API errors"""
        mock_client.messages.create.side_effect = Exception("API Error")

        result = parse_cv_with_llm(sample_cv_text)

        assert result is None

    @patch('app.services.llm.client', None)
    def test_parse_cv_no_api_key(self, sample_cv_text):
        """Test handling when API key is not configured"""
        result = parse_cv_with_llm(sample_cv_text)

        assert result is None

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_parse_cv_prompt_structure(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text, mock_claude_response):
        """Test that the prompt has correct structure and instructions"""
        mock_client.messages.create.return_value = mock_claude_response

        parse_cv_with_llm(sample_cv_text)

        call_kwargs = mock_client.messages.create.call_args[1]
        prompt = call_kwargs["messages"][0]["content"]

        # Verify prompt contains key elements
        assert "Extract structured information" in prompt
        assert "JSON" in prompt
        assert "name" in prompt
        assert "skills" in prompt
        assert "experience" in prompt
        assert "education" in prompt
        assert sample_cv_text in prompt


class TestJobRequirementExtraction:
    """Test job requirement extraction with Claude Haiku"""

    @pytest.fixture
    def mock_job_response(self):
        """Mock successful Claude API response for job extraction"""
        return Mock(
            content=[
                Mock(
                    text=json.dumps({
                        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                        "nice_to_have_skills": ["Docker", "AWS"],
                        "experience_years_min": 3,
                        "experience_years_max": 5,
                        "education": "Bachelor's degree in Computer Science",
                        "languages": ["English"],
                        "job_type": "permanent",
                        "remote_type": "full"
                    })
                )
            ]
        )

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_extract_job_requirements_success(self, mock_client, mock_cache_set, mock_cache_get, mock_job_response):
        """Test successful job requirement extraction"""
        mock_client.messages.create.return_value = mock_job_response

        result = extract_job_requirements(
            job_title="Senior Python Developer",
            job_company="Tech Corp",
            job_description="Looking for experienced Python developer with FastAPI and PostgreSQL experience..."
        )

        assert result is not None
        assert "Python" in result["required_skills"]
        assert "FastAPI" in result["required_skills"]
        assert "Docker" in result["nice_to_have_skills"]
        assert result["experience_years_min"] == 3
        assert result["experience_years_max"] == 5
        assert result["job_type"] == "permanent"
        assert result["remote_type"] == "full"

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_extract_job_requirements_prompt_structure(self, mock_client, mock_cache_set, mock_cache_get, mock_job_response):
        """Test that job extraction prompt is correctly structured"""
        mock_client.messages.create.return_value = mock_job_response

        extract_job_requirements(
            job_title="Backend Engineer",
            job_company="Startup Inc",
            job_description="We need a backend engineer"
        )

        call_kwargs = mock_client.messages.create.call_args[1]
        prompt = call_kwargs["messages"][0]["content"]

        # Verify prompt contains required elements
        assert "Backend Engineer" in prompt
        assert "Startup Inc" in prompt
        assert "We need a backend engineer" in prompt
        assert "required_skills" in prompt
        assert "nice_to_have_skills" in prompt
        assert "remote_type" in prompt

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_extract_job_requirements_with_nulls(self, mock_client, mock_cache_set, mock_cache_get):
        """Test extraction when some fields are null"""
        mock_response = Mock(
            content=[
                Mock(
                    text=json.dumps({
                        "required_skills": ["Python"],
                        "nice_to_have_skills": [],
                        "experience_years_min": None,
                        "experience_years_max": None,
                        "education": None,
                        "languages": ["English"],
                        "job_type": "contract",
                        "remote_type": "hybrid"
                    })
                )
            ]
        )
        mock_client.messages.create.return_value = mock_response

        result = extract_job_requirements(
            job_title="Developer",
            job_company="Company",
            job_description="Description"
        )

        assert result is not None
        assert result["experience_years_min"] is None
        assert result["experience_years_max"] is None
        assert result["education"] is None

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_extract_job_invalid_json(self, mock_client, mock_cache_set, mock_cache_get):
        """Test handling invalid JSON in job extraction"""
        mock_response = Mock(
            content=[Mock(text="Not valid JSON")]
        )
        mock_client.messages.create.return_value = mock_response

        result = extract_job_requirements("Title", "Company", "Description")

        assert result is None


class TestLLMServiceConfiguration:
    """Test LLM service configuration and error handling"""

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_uses_haiku_model(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text):
        """Verify that Haiku model is used for extraction (cost optimization)"""
        mock_response = Mock(
            content=[Mock(text='{"name": "Test", "skills": [], "experience": [], "education": [], "years_of_experience": 0}')]
        )
        mock_client.messages.create.return_value = mock_response

        parse_cv_with_llm(sample_cv_text)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_uses_zero_temperature(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text):
        """Verify that temperature is 0 for deterministic extraction"""
        mock_response = Mock(
            content=[Mock(text='{"name": "Test", "skills": [], "experience": [], "education": [], "years_of_experience": 0}')]
        )
        mock_client.messages.create.return_value = mock_response

        parse_cv_with_llm(sample_cv_text)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 0

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_max_tokens_reasonable(self, mock_client, mock_cache_set, mock_cache_get, sample_cv_text):
        """Verify max_tokens is set appropriately"""
        mock_response = Mock(
            content=[Mock(text='{"name": "Test", "skills": [], "experience": [], "education": [], "years_of_experience": 0}')]
        )
        mock_client.messages.create.return_value = mock_response

        parse_cv_with_llm(sample_cv_text)

        call_kwargs = mock_client.messages.create.call_args[1]
        # Should have reasonable max_tokens for CV parsing
        assert call_kwargs["max_tokens"] >= 1024
        assert call_kwargs["max_tokens"] <= 4096


class TestLLMCaching:
    """Test caching functionality for LLM service"""

    @patch('app.services.llm.client')
    def test_cv_parse_cache_hit(self, mock_client):
        """Test CV parsing returns cached result on cache hit"""
        cached_data = {
            "name": "Cached User",
            "email": "cached@example.com",
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "years_of_experience": 5
        }

        with patch('app.services.llm.cache_get', return_value=cached_data):
            result = parse_cv_with_llm("Sample CV text")

            assert result == cached_data
            assert result["name"] == "Cached User"
            # Verify no API call was made
            mock_client.messages.create.assert_not_called()

    @patch('app.services.llm.client')
    def test_job_extract_cache_hit(self, mock_client):
        """Test job extraction returns cached result on cache hit"""
        cached_data = {
            "required_skills": ["Python", "Django"],
            "nice_to_have_skills": ["Docker"],
            "experience_years_min": 2,
            "experience_years_max": 4,
            "remote_type": "hybrid"
        }

        with patch('app.services.llm.cache_get', return_value=cached_data):
            result = extract_job_requirements("Developer", "Company", "Description")

            assert result == cached_data
            assert "Python" in result["required_skills"]
            # Verify no API call was made
            mock_client.messages.create.assert_not_called()

    @patch('app.services.llm.client', None)
    def test_job_extract_no_client(self):
        """Test job extraction when API client is not configured"""
        result = extract_job_requirements("Developer", "Company", "Description")
        assert result is None

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_cv_parse_json_prefix(self, mock_client, mock_cache_set, mock_cache_get):
        """Test CV parsing handles 'json' prefix in response"""
        json_data = '{"name": "Test", "skills": [], "experience": [], "education": [], "years_of_experience": 0}'
        # Response with json prefix after code block removal
        mock_response = Mock(
            content=[Mock(text=f"json\n{json_data}")]
        )
        mock_client.messages.create.return_value = mock_response

        result = parse_cv_with_llm("CV text")

        assert result is not None
        assert result["name"] == "Test"

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_job_extract_json_prefix(self, mock_client, mock_cache_set, mock_cache_get):
        """Test job extraction handles 'json' prefix in response"""
        json_data = '{"required_skills": ["Python"], "nice_to_have_skills": [], "remote_type": "full"}'
        mock_response = Mock(
            content=[Mock(text=f"json\n{json_data}")]
        )
        mock_client.messages.create.return_value = mock_response

        result = extract_job_requirements("Dev", "Co", "Desc")

        assert result is not None
        assert result["remote_type"] == "full"

    @patch('app.services.llm.cache_get', return_value=None)
    @patch('app.services.llm.cache_set')
    @patch('app.services.llm.client')
    def test_job_extract_api_error(self, mock_client, mock_cache_set, mock_cache_get):
        """Test job extraction handles API errors gracefully"""
        mock_client.messages.create.side_effect = Exception("API Error")

        result = extract_job_requirements("Dev", "Co", "Desc")

        assert result is None
