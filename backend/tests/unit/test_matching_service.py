"""
Unit tests for matching service
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.matching import (
    normalize_skill,
    calculate_skill_match,
    calculate_work_type_match,
    should_match_remote_type,
    should_match_eligibility,
    calculate_location_match,
    calculate_salary_match,
    calculate_experience_match,
    calculate_title_match,
)


class TestNormalizeSkill:
    """Test skill normalization"""

    def test_lowercase_conversion(self):
        """Test that skills are lowercased"""
        assert normalize_skill("Python") == "python"
        assert normalize_skill("JavaScript") == "javascript"

    def test_whitespace_stripped(self):
        """Test that whitespace is stripped"""
        assert normalize_skill("  Python  ") == "python"
        assert normalize_skill("\tJava\n") == "java"

    def test_combined_normalization(self):
        """Test combined lowercase and strip"""
        assert normalize_skill("  REACT  ") == "react"


class TestCalculateSkillMatch:
    """Test skill match calculation"""

    def test_no_user_skills(self):
        """Test when user has no skills"""
        job_requirements = {"required_skills": ["Python", "Django"]}
        score, matches, missing = calculate_skill_match([], job_requirements)

        assert score == 0.0
        assert matches == []
        assert missing == ["Python", "Django"]

    def test_all_skills_match(self):
        """Test when all required skills match"""
        user_skills = ["Python", "Django", "PostgreSQL"]
        job_requirements = {"required_skills": ["Python", "Django"]}

        score, matches, missing = calculate_skill_match(user_skills, job_requirements)

        assert score == 80.0  # 100% of required skills = 80 points
        assert len(matches) == 2
        assert missing == []

    def test_partial_skill_match(self):
        """Test when some skills match"""
        user_skills = ["Python", "JavaScript"]
        job_requirements = {
            "required_skills": ["Python", "Django"],
            "nice_to_have_skills": []
        }

        score, matches, missing = calculate_skill_match(user_skills, job_requirements)

        assert score == 40.0  # 50% of required skills = 40 points
        assert "Python" in matches
        assert "Django" in missing

    def test_nice_to_have_skills(self):
        """Test nice-to-have skills contribute to score"""
        user_skills = ["Python", "Docker"]
        job_requirements = {
            "required_skills": ["Python"],
            "nice_to_have_skills": ["Docker", "Kubernetes"]
        }

        score, matches, missing = calculate_skill_match(user_skills, job_requirements)

        # 100% required (80) + 50% nice-to-have (10) = 90
        assert score == 90.0
        assert "Python" in matches
        assert "Docker" in matches
        assert missing == []

    def test_no_required_skills(self):
        """Test when job has no required skills"""
        user_skills = ["Python"]
        job_requirements = {
            "required_skills": [],
            "nice_to_have_skills": ["Python", "Django"]
        }

        score, matches, missing = calculate_skill_match(user_skills, job_requirements)

        assert score == 50.0  # 50% of nice-to-have

    def test_no_skills_specified(self):
        """Test when job has no skill requirements at all"""
        user_skills = ["Python"]
        job_requirements = {}

        score, matches, missing = calculate_skill_match(user_skills, job_requirements)

        assert score == 50.0  # Default neutral score

    def test_case_insensitive_matching(self):
        """Test that skill matching is case insensitive"""
        user_skills = ["python", "DJANGO"]
        job_requirements = {"required_skills": ["Python", "django"]}

        score, matches, missing = calculate_skill_match(user_skills, job_requirements)

        assert score == 80.0


class TestCalculateWorkTypeMatch:
    """Test work type matching"""

    def test_no_preference(self):
        """Test when user has no work type preference"""
        job = MagicMock()
        job.job_type = "permanent"

        score = calculate_work_type_match({}, job)
        assert score == 100.0

    def test_matching_work_type(self):
        """Test when work type matches preference"""
        job = MagicMock()
        job.job_type = "contract"

        score = calculate_work_type_match({"job_types": ["contract", "freelance"]}, job)
        assert score == 100.0

    def test_non_matching_work_type(self):
        """Test when work type doesn't match"""
        job = MagicMock()
        job.job_type = "permanent"

        score = calculate_work_type_match({"job_types": ["contract"]}, job)
        assert score == 0.0


class TestShouldMatchRemoteType:
    """Test remote type filtering"""

    def test_no_preference(self):
        """Test when user has no remote preference"""
        job = MagicMock()
        job.remote_type = "full"

        assert should_match_remote_type({}, job) is True

    def test_matching_remote_type(self):
        """Test when remote type matches"""
        job = MagicMock()
        job.remote_type = "full"

        assert should_match_remote_type({"remote_types": ["full", "hybrid"]}, job) is True

    def test_non_matching_remote_type(self):
        """Test when remote type doesn't match"""
        job = MagicMock()
        job.remote_type = "onsite"

        assert should_match_remote_type({"remote_types": ["full"]}, job) is False


class TestShouldMatchEligibility:
    """Test employment eligibility filtering"""

    def test_no_region_preference(self):
        """Test when user has no region preference"""
        job = MagicMock()
        job.eligible_regions = ["USA"]
        job.visa_sponsorship = None

        assert should_match_eligibility({}, job) is True

    def test_worldwide_job(self):
        """Test job that accepts worldwide applicants"""
        job = MagicMock()
        job.eligible_regions = ["Worldwide"]
        job.visa_sponsorship = None

        assert should_match_eligibility({"eligible_regions": ["Europe"]}, job) is True

    def test_worldwide_user(self):
        """Test user who can work worldwide"""
        job = MagicMock()
        job.eligible_regions = ["USA"]
        job.visa_sponsorship = None

        assert should_match_eligibility({"eligible_regions": ["Worldwide"]}, job) is True

    def test_matching_region(self):
        """Test matching region"""
        job = MagicMock()
        job.eligible_regions = ["USA", "Europe"]
        job.visa_sponsorship = None

        assert should_match_eligibility({"eligible_regions": ["europe"]}, job) is True

    def test_non_matching_region(self):
        """Test non-matching region"""
        job = MagicMock()
        job.eligible_regions = ["USA"]
        job.visa_sponsorship = None

        assert should_match_eligibility({"eligible_regions": ["Asia"]}, job) is False

    def test_needs_visa_but_not_offered(self):
        """Test when user needs visa but job doesn't offer"""
        job = MagicMock()
        job.eligible_regions = None
        job.visa_sponsorship = 0  # No sponsorship

        assert should_match_eligibility({"needs_visa_sponsorship": True}, job) is False

    def test_needs_visa_and_offered(self):
        """Test when user needs visa and job offers it"""
        job = MagicMock()
        job.eligible_regions = None
        job.visa_sponsorship = 1  # Offers sponsorship

        assert should_match_eligibility({"needs_visa_sponsorship": True}, job) is True

    def test_needs_visa_unknown(self):
        """Test when visa sponsorship is unknown"""
        job = MagicMock()
        job.eligible_regions = None
        job.visa_sponsorship = None  # Unknown

        assert should_match_eligibility({"needs_visa_sponsorship": True}, job) is True


class TestCalculateLocationMatch:
    """Test location matching"""

    def test_no_preference(self):
        """Test when user has no location preference"""
        job = MagicMock()
        job.location = "San Francisco, CA"
        job.remote_type = "onsite"

        score = calculate_location_match({}, job)
        assert score == 100.0

    def test_remote_preference_full_remote(self):
        """Test remote preference with fully remote job"""
        job = MagicMock()
        job.location = "Anywhere"
        job.remote_type = "full"

        score = calculate_location_match({"preferred_countries": ["Remote"]}, job)
        assert score == 100.0

    def test_matching_country(self):
        """Test matching country preference"""
        job = MagicMock()
        job.location = "Berlin, Germany"
        job.remote_type = "hybrid"

        score = calculate_location_match({"preferred_countries": ["Germany"]}, job)
        assert score == 100.0

    def test_non_matching_location(self):
        """Test non-matching location"""
        job = MagicMock()
        job.location = "Tokyo, Japan"
        job.remote_type = "onsite"

        score = calculate_location_match({"preferred_countries": ["USA"]}, job)
        assert score == 30.0


class TestCalculateSalaryMatch:
    """Test salary matching"""

    def test_no_salary_preference(self):
        """Test when user has no salary preference"""
        job = MagicMock()
        job.salary_min = 100000
        job.salary_max = 150000

        score = calculate_salary_match({}, job)
        assert score == 100.0

    def test_no_job_salary_info(self):
        """Test when job has no salary info"""
        job = MagicMock()
        job.salary_min = None
        job.salary_max = None

        score = calculate_salary_match({"min_salary": 100000}, job)
        assert score == 50.0

    def test_salary_meets_minimum(self):
        """Test when salary meets minimum requirement"""
        job = MagicMock()
        job.salary_min = 100000
        job.salary_max = 150000

        score = calculate_salary_match({"min_salary": 100000}, job)
        assert score == 100.0

    def test_salary_close_to_minimum(self):
        """Test when salary is close to minimum (within 90%)"""
        job = MagicMock()
        job.salary_min = 95000
        job.salary_max = None

        score = calculate_salary_match({"min_salary": 100000}, job)
        assert score == 80.0

    def test_salary_somewhat_close(self):
        """Test when salary is somewhat close (within 80%)"""
        job = MagicMock()
        job.salary_min = 85000
        job.salary_max = None

        score = calculate_salary_match({"min_salary": 100000}, job)
        assert score == 60.0

    def test_salary_below_expectations(self):
        """Test when salary is well below expectations"""
        job = MagicMock()
        job.salary_min = 60000
        job.salary_max = None

        score = calculate_salary_match({"min_salary": 100000}, job)
        assert score == 30.0


class TestCalculateExperienceMatch:
    """Test experience matching"""

    def test_no_experience_info(self):
        """Test when no experience info available"""
        user = MagicMock()
        user.experience_years = None

        score = calculate_experience_match(user, {})
        assert score == 50.0

    def test_no_job_experience_requirement(self):
        """Test when job has no experience requirement"""
        user = MagicMock()
        user.experience_years = 5

        score = calculate_experience_match(user, {})
        assert score == 50.0

    def test_perfect_experience_match(self):
        """Test when experience is within range"""
        user = MagicMock()
        user.experience_years = 5

        score = calculate_experience_match(user, {
            "experience_years_min": 3,
            "experience_years_max": 7
        })
        assert score == 100.0

    def test_slightly_under_experienced(self):
        """Test when user is slightly under-experienced"""
        user = MagicMock()
        user.experience_years = 2

        score = calculate_experience_match(user, {"experience_years_min": 3})
        assert score == 80.0

    def test_under_experienced(self):
        """Test when user is under-experienced by 2 years"""
        user = MagicMock()
        user.experience_years = 1

        score = calculate_experience_match(user, {"experience_years_min": 3})
        assert score == 60.0

    def test_very_under_experienced(self):
        """Test when user is very under-experienced"""
        user = MagicMock()
        user.experience_years = 1

        score = calculate_experience_match(user, {"experience_years_min": 5})
        assert score == 40.0

    def test_over_experienced(self):
        """Test when user is over-experienced"""
        user = MagicMock()
        user.experience_years = 15

        score = calculate_experience_match(user, {
            "experience_years_min": 3,
            "experience_years_max": 7
        })
        assert score == 90.0


class TestCalculateTitleMatch:
    """Test job title matching"""

    def test_no_target_roles(self):
        """Test when user has no target roles"""
        user = MagicMock()
        user.preferences = {}
        job = MagicMock()
        job.title = "Software Engineer"

        score = calculate_title_match(user, job)
        assert score == 50.0

    def test_matching_engineer_role(self):
        """Test matching engineer role"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Backend Developer"]}
        job = MagicMock()
        job.title = "Senior Software Engineer"

        score = calculate_title_match(user, job)
        # Both are engineer roles, should score well
        assert score > 50.0

    def test_inferred_roles_from_cv(self):
        """Test target roles inferred from CV experience"""
        user = MagicMock()
        user.preferences = {
            "parsed_cv": {
                "experience": [
                    {"title": "Senior Developer"},
                    {"title": "Software Engineer"}
                ]
            }
        }
        job = MagicMock()
        job.title = "Backend Engineer"

        score = calculate_title_match(user, job)
        # Should use CV titles and match engineer role
        assert score > 50.0
