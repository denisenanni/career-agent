"""
Unit tests for JobScrapedData schema validation
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.job import JobScrapedData, sanitize_html_content


class TestJobScrapedDataValidation:
    """Test JobScrapedData validation logic"""

    def test_valid_job_data(self):
        """Test validation passes with valid job data"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job/123",
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "description": "Great opportunity for a Python developer",
            "salary_min": 100000,
            "salary_max": 150000,
            "salary_currency": "USD",
            "location": "Remote",
            "remote_type": "full",
            "job_type": "permanent",
            "tags": ["python", "django", "postgresql"],
        }

        validated = JobScrapedData(**job_data)

        assert validated.source_id == "job123"
        assert validated.title == "Senior Python Developer"
        assert validated.salary_min == 100000
        assert validated.tags == ["python", "django", "postgresql"]

    def test_minimal_required_fields(self):
        """Test validation with only required fields"""
        job_data = {
            "source_id": "job456",
            "url": "https://example.com/job/456",
            "title": "Developer",
            "company": "Company",
            "description": "Job description",
        }

        validated = JobScrapedData(**job_data)

        assert validated.source_id == "job456"
        assert validated.salary_currency is None  # default (None when no salary)
        assert validated.location == "Remote"  # default
        assert validated.remote_type == "full"  # default
        assert validated.job_type == "permanent"  # default
        assert validated.tags == []  # default

    def test_missing_required_field_source_id(self):
        """Test validation fails without source_id"""
        job_data = {
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "source_id" in str(exc_info.value)

    def test_missing_required_field_url(self):
        """Test validation fails without url"""
        job_data = {
            "source_id": "job123",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "url" in str(exc_info.value)

    def test_invalid_url_format(self):
        """Test validation fails with invalid URL"""
        job_data = {
            "source_id": "job123",
            "url": "not-a-valid-url",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "Invalid URL format" in str(exc_info.value)

    def test_valid_url_formats(self):
        """Test various valid URL formats"""
        valid_urls = [
            "https://example.com/job/123",
            "http://example.com/job",
            "https://subdomain.example.com/path",
            "https://example.com:8080/job",
            "http://localhost:3000/job",
            "https://192.168.1.1/job",
        ]

        for url in valid_urls:
            job_data = {
                "source_id": "job123",
                "url": url,
                "title": "Developer",
                "company": "Company",
                "description": "Description",
            }
            validated = JobScrapedData(**job_data)
            assert validated.url == url

    def test_title_too_long(self):
        """Test validation fails when title exceeds max length"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "X" * 501,  # MAX_TITLE_LENGTH is 500
            "company": "Company",
            "description": "Description",
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "title" in str(exc_info.value)

    def test_description_too_long(self):
        """Test validation fails when description exceeds max length"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "X" * 50001,  # MAX_DESCRIPTION_LENGTH is 50000
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "description" in str(exc_info.value)

    def test_salary_range_validation(self):
        """Test salary_max must be >= salary_min"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "salary_min": 150000,
            "salary_max": 100000,  # Less than min
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "salary_max" in str(exc_info.value)
        assert "salary_min" in str(exc_info.value)

    def test_negative_salary(self):
        """Test validation fails with negative salary"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "salary_min": -1000,
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "salary_min" in str(exc_info.value)

    def test_tags_validation_removes_empty_strings(self):
        """Test empty strings are removed from tags"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "tags": ["python", "", "  ", "django", ""],
        }

        validated = JobScrapedData(**job_data)

        assert validated.tags == ["python", "django"]
        assert "" not in validated.tags

    def test_tags_whitespace_trimmed(self):
        """Test tags have whitespace trimmed"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "tags": ["  python  ", " django", "postgresql  "],
        }

        validated = JobScrapedData(**job_data)

        assert validated.tags == ["python", "django", "postgresql"]

    def test_tag_too_long(self):
        """Test validation fails when tag exceeds max length"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "tags": ["x" * 101],  # MAX_TAG_LENGTH is 100
        }

        with pytest.raises(ValidationError) as exc_info:
            JobScrapedData(**job_data)

        assert "Tag exceeds max length" in str(exc_info.value)

    def test_whitespace_stripped_from_text_fields(self):
        """Test leading/trailing whitespace is stripped from text fields"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "  Developer  ",
            "company": "  Tech Corp  ",
            "description": "  Great job  ",
        }

        validated = JobScrapedData(**job_data)

        assert validated.title == "Developer"
        assert validated.company == "Tech Corp"
        assert validated.description == "Great job"


class TestHTMLSanitization:
    """Test HTML sanitization function"""

    def test_sanitize_simple_string_with_html(self):
        """Test HTML entities are escaped in strings"""
        result = sanitize_html_content("<script>alert('xss')</script>")
        # html.escape also escapes quotes to &#x27;
        assert result == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"

    def test_sanitize_string_without_html(self):
        """Test strings without HTML are unchanged"""
        result = sanitize_html_content("Just a normal string")
        assert result == "Just a normal string"

    def test_sanitize_none(self):
        """Test None returns None"""
        result = sanitize_html_content(None)
        assert result is None

    def test_sanitize_dict(self):
        """Test dict values are sanitized"""
        data = {
            "safe": "normal text",
            "unsafe": "<script>alert(1)</script>",
            "nested": {"inner": "<b>bold</b>"},
        }

        result = sanitize_html_content(data)

        assert result["safe"] == "normal text"
        assert result["unsafe"] == "&lt;script&gt;alert(1)&lt;/script&gt;"
        assert result["nested"]["inner"] == "&lt;b&gt;bold&lt;/b&gt;"

    def test_sanitize_list(self):
        """Test list items are sanitized"""
        data = ["safe text", "<img src=x>", "another safe"]

        result = sanitize_html_content(data)

        assert result[0] == "safe text"
        assert result[1] == "&lt;img src=x&gt;"
        assert result[2] == "another safe"

    def test_sanitize_skips_technical_fields(self):
        """Test technical fields are not sanitized for performance"""
        data = {
            "id": "<should-not-escape>",
            "timestamp": "<should-not-escape>",
            "created_at": "<should-not-escape>",
            "user_input": "<should-escape>",
        }

        result = sanitize_html_content(data)

        # Technical fields not sanitized
        assert result["id"] == "<should-not-escape>"
        assert result["timestamp"] == "<should-not-escape>"
        assert result["created_at"] == "<should-not-escape>"

        # User content sanitized
        assert result["user_input"] == "&lt;should-escape&gt;"

    def test_sanitize_max_depth(self):
        """Test sanitization stops at max depth"""
        deep_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "<script>deep</script>",
                    }
                }
            }
        }

        # With max_depth=3, level4 won't be sanitized
        result = sanitize_html_content(deep_data, max_depth=3)

        # At depth 3, sanitization stops
        assert result["level1"]["level2"]["level3"]["level4"] == "<script>deep</script>"

    def test_sanitize_large_list_optimization(self):
        """Test large lists only process first 100 items"""
        # Create list with 150 items
        large_list = ["<script>item</script>"] * 150

        result = sanitize_html_content(large_list)

        # First 100 should be sanitized
        assert result[0] == "&lt;script&gt;item&lt;/script&gt;"
        assert result[99] == "&lt;script&gt;item&lt;/script&gt;"

        # Items after 100 should be unchanged (optimization)
        assert result[100] == "<script>item</script>"
        assert result[149] == "<script>item</script>"

    def test_raw_data_sanitization_in_schema(self):
        """Test raw_data field is sanitized when creating JobScrapedData"""
        job_data = {
            "source_id": "job123",
            "url": "https://example.com/job",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "raw_data": {
                "original_title": "<b>Bold Title</b>",
                "metadata": {"posted": "<script>xss</script>"},
            },
        }

        validated = JobScrapedData(**job_data)

        assert validated.raw_data["original_title"] == "&lt;b&gt;Bold Title&lt;/b&gt;"
        assert validated.raw_data["metadata"]["posted"] == "&lt;script&gt;xss&lt;/script&gt;"
