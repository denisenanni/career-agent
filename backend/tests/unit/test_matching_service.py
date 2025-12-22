"""
Unit tests for matching service
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.matching import (
    calculate_skill_match,
    calculate_work_type_match,
    should_match_remote_type,
    should_match_eligibility,
    should_match_seniority,
    detect_job_seniority,
    calculate_freshness_score,
    calculate_location_match,
    calculate_salary_match,
    calculate_experience_match,
    calculate_title_match,
)
from app.utils.skill_aliases import normalize_skill
from app.utils.skill_clusters import calculate_skill_similarity, are_skills_related, get_related_skills
from datetime import datetime, timezone, timedelta


class TestNormalizeSkill:
    """Test skill normalization with alias mapping"""

    def test_canonical_names(self):
        """Test that known skills are mapped to canonical names"""
        assert normalize_skill("Python") == "Python"
        assert normalize_skill("python") == "Python"
        assert normalize_skill("PYTHON") == "Python"
        assert normalize_skill("JavaScript") == "JavaScript"
        assert normalize_skill("js") == "JavaScript"
        assert normalize_skill("JS") == "JavaScript"

    def test_whitespace_stripped(self):
        """Test that whitespace is stripped before normalization"""
        assert normalize_skill("  Python  ") == "Python"
        assert normalize_skill("\tJava\n") == "Java"
        assert normalize_skill("  js  ") == "JavaScript"

    def test_alias_resolution(self):
        """Test that aliases are resolved to canonical names"""
        # JavaScript ecosystem
        assert normalize_skill("ts") == "TypeScript"
        assert normalize_skill("reactjs") == "React"
        assert normalize_skill("react.js") == "React"
        assert normalize_skill("nodejs") == "Node.js"
        assert normalize_skill("node") == "Node.js"

        # Databases
        assert normalize_skill("postgres") == "PostgreSQL"
        assert normalize_skill("pg") == "PostgreSQL"
        assert normalize_skill("mongo") == "MongoDB"

        # Cloud
        assert normalize_skill("aws") == "AWS"
        assert normalize_skill("gcp") == "Google Cloud"
        assert normalize_skill("k8s") == "Kubernetes"

    def test_unknown_skills_preserved(self):
        """Test that unknown skills are preserved with original case"""
        assert normalize_skill("SomeUnknownSkill") == "SomeUnknownSkill"
        assert normalize_skill("custom framework") == "custom framework"


class TestCalculateSkillMatch:
    """Test skill match calculation"""

    def test_no_user_skills(self):
        """Test when user has no skills"""
        job_requirements = {"required_skills": ["Python", "Django"]}
        score, matches, missing, related = calculate_skill_match([], job_requirements)

        assert score == 0.0
        assert matches == []
        assert missing == ["Python", "Django"]
        assert related == []

    def test_all_skills_match(self):
        """Test when all required skills match"""
        user_skills = ["Python", "Django", "PostgreSQL"]
        job_requirements = {"required_skills": ["Python", "Django"]}

        score, matches, missing, related = calculate_skill_match(user_skills, job_requirements)

        assert score == 80.0  # 100% of required skills = 80 points
        assert len(matches) == 2
        assert missing == []
        assert related == []

    def test_partial_skill_match(self):
        """Test when some skills match"""
        user_skills = ["Python", "JavaScript"]
        job_requirements = {
            "required_skills": ["Python", "Django"],
            "nice_to_have_skills": []
        }

        score, matches, missing, related = calculate_skill_match(user_skills, job_requirements)

        # Semantic matching: Python matches Python (100%), Django related via cluster (50%)
        # 1 exact + 0.5 related = 1.5/2 = 75% of required = 60 points
        assert score == 60.0
        assert "Python" in matches
        # Django is now related (Python and Django are in same cluster)
        assert "Django" in related

    def test_nice_to_have_skills(self):
        """Test nice-to-have skills contribute to score"""
        user_skills = ["Python", "Docker"]
        job_requirements = {
            "required_skills": ["Python"],
            "nice_to_have_skills": ["Docker", "Kubernetes"]
        }

        score, matches, missing, related = calculate_skill_match(user_skills, job_requirements)

        # 100% required (80) + Docker matches (10) + K8s related via Docker cluster (5) = 95
        # Docker and Kubernetes are in same cluster
        assert score >= 90.0
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

        score, matches, missing, related = calculate_skill_match(user_skills, job_requirements)

        # Python exact (100%) + Django related (50%) = 75% of nice-to-have
        assert score >= 50.0

    def test_no_skills_specified(self):
        """Test when job has no skill requirements at all"""
        user_skills = ["Python"]
        job_requirements = {}

        score, matches, missing, related = calculate_skill_match(user_skills, job_requirements)

        assert score == 50.0  # Default neutral score

    def test_case_insensitive_matching(self):
        """Test that skill matching is case insensitive"""
        user_skills = ["python", "DJANGO"]
        job_requirements = {"required_skills": ["Python", "django"]}

        score, matches, missing, related = calculate_skill_match(user_skills, job_requirements)

        assert score == 80.0

    def test_related_skills_via_cluster(self):
        """Test semantic matching via skill clusters"""
        # User has Flask, job requires Django - both in python_web cluster
        user_skills = ["Python", "Flask"]
        job_requirements = {
            "required_skills": ["Python", "Django"],
            "nice_to_have_skills": []
        }

        score, matches, missing, related = calculate_skill_match(user_skills, job_requirements)

        # Python exact (1.0) + Django related via Flask (0.5) = 1.5/2 = 75% = 60 points
        assert score == 60.0
        assert "Python" in matches
        assert "Django" in related
        assert missing == []  # Django is related, not missing


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

    def test_ic_engineer_vs_manager_role(self):
        """Test IC engineer vs pure management role"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Software Engineer", "Backend Developer"]}
        job = MagicMock()
        job.title = "Product Manager"  # Pure management role without engineer keyword

        score = calculate_title_match(user, job)
        # IC engineer shouldn't match pure management roles
        assert score == 10.0

    def test_manager_vs_ic_role(self):
        """Test manager doesn't match pure IC roles"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Engineering Manager", "Technical Lead"]}
        job = MagicMock()
        job.title = "Software Engineer"  # IC role

        score = calculate_title_match(user, job)
        # Manager shouldn't match pure IC roles
        assert score == 30.0

    def test_designer_role_match(self):
        """Test designer role matching"""
        user = MagicMock()
        user.preferences = {"target_roles": ["UX Designer", "Product Designer"]}
        job = MagicMock()
        job.title = "Senior UI Designer"

        score = calculate_title_match(user, job)
        # Designer roles should match
        assert score == 90.0

    def test_data_role_match(self):
        """Test data role matching"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Data Scientist", "ML Engineer"]}
        job = MagicMock()
        job.title = "Machine Learning Engineer"

        score = calculate_title_match(user, job)
        # Data/ML roles should match
        assert score == 90.0

    def test_devops_role_match(self):
        """Test DevOps role matching"""
        user = MagicMock()
        user.preferences = {"target_roles": ["DevOps Engineer"]}
        job = MagicMock()
        job.title = "DevOps Engineer"

        score = calculate_title_match(user, job)
        # DevOps roles should match
        assert score == 90.0

    def test_keyword_overlap_good(self):
        """Test good keyword overlap in titles"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Frontend React Developer"]}
        job = MagicMock()
        job.title = "React JavaScript Developer"

        score = calculate_title_match(user, job)
        # Both have "developer", "react" keywords (2+ overlap), should score 70
        assert score >= 70.0

    def test_keyword_overlap_some(self):
        """Test some keyword overlap"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Python Developer"]}
        job = MagicMock()
        job.title = "Python Architect"

        score = calculate_title_match(user, job)
        # 1 keyword overlap should score 50
        assert score == 50.0

    def test_no_keyword_overlap(self):
        """Test no keyword overlap"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Python Developer"]}
        job = MagicMock()
        job.title = "Java Architect"

        score = calculate_title_match(user, job)
        # No overlap should score 20
        assert score == 20.0

    def test_seniority_match_bonus(self):
        """Test seniority match gives bonus"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Senior Software Engineer"]}
        job = MagicMock()
        job.title = "Senior Backend Developer"

        score = calculate_title_match(user, job)
        # Should get engineer match (90) + seniority bonus (10) = 100
        assert score == 100.0

    def test_seniority_mismatch_penalty(self):
        """Test seniority mismatch gives penalty"""
        user = MagicMock()
        user.preferences = {"target_roles": ["Senior Software Engineer"]}
        job = MagicMock()
        job.title = "Software Engineer"  # No senior

        score = calculate_title_match(user, job)
        # Should get engineer match (90) - seniority penalty (10) = 80
        assert score == 80.0


class TestCalculateMatchScore:
    """Test overall match score calculation"""

    def test_calculate_match_score_all_components(self):
        """Test that calculate_match_score combines all scoring components"""
        from app.services.matching import calculate_match_score

        user = MagicMock()
        user.skills = ["Python", "Django"]
        user.preferences = {"min_salary": 100000}
        user.experience_years = 5

        job = MagicMock()
        job.title = "Senior Python Developer"
        job.salary_min = 120000
        job.salary_max = None
        job.location = "Remote"
        job.remote_type = "full"
        job.job_type = "permanent"
        # Add date fields for freshness calculation
        job.posted_at = datetime.now(timezone.utc) - timedelta(days=3)
        job.scraped_at = None
        job.created_at = None

        job_requirements = {
            "required_skills": ["Python", "Django"],
            "nice_to_have_skills": [],
            "experience_years_min": 3,
            "experience_years_max": 7
        }

        score, analysis = calculate_match_score(user, job, job_requirements)

        # Should return score and analysis dict
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert "overall_score" in analysis
        assert "skill_score" in analysis
        assert "title_score" in analysis
        assert "freshness_score" in analysis  # New field
        assert "matching_skills" in analysis
        assert "missing_skills" in analysis
        assert "related_skills" in analysis  # New field


class TestCreateMatchForJob:
    """Test create_match_for_job function error paths"""

    @pytest.mark.asyncio
    @patch('app.services.matching.extract_job_requirements')
    async def test_create_match_llm_returns_none(self, mock_extract):
        """Test when LLM fails to extract requirements"""
        from app.services.matching import create_match_for_job

        mock_extract.return_value = None

        db = MagicMock()
        # First query checks for rejected/hidden - return None (no prior rejection)
        db.query.return_value.filter.return_value.first.return_value = None

        user = MagicMock()
        user.id = 1
        user.skills = ["Python"]
        user.preferences = {}

        job = MagicMock()
        job.id = 1
        job.title = "Developer"
        job.company = "Test Co"
        job.description = "Test"
        job.remote_type = "full"
        job.eligible_regions = None
        job.visa_sponsorship = None

        result = await create_match_for_job(db, user, job)

        # Should return None when LLM fails
        assert result is None
        mock_extract.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.matching.extract_job_requirements')
    async def test_create_match_score_below_threshold(self, mock_extract):
        """Test when match score is below threshold"""
        from app.services.matching import create_match_for_job

        mock_extract.return_value = {
            "required_skills": ["Java", "Spring"],  # User has Python, not Java
            "nice_to_have_skills": []
        }

        db = MagicMock()
        # First query checks for rejected/hidden - return None (no prior rejection)
        db.query.return_value.filter.return_value.first.return_value = None

        user = MagicMock()
        user.id = 1
        user.skills = ["Python"]
        user.preferences = {}
        user.experience_years = None

        job = MagicMock()
        job.id = 1
        job.title = "Java Developer"
        job.company = "Test Co"
        job.description = "Java role"
        job.remote_type = "full"
        job.salary_min = None
        job.salary_max = None
        job.location = None
        job.eligible_regions = None
        job.visa_sponsorship = None
        job.posted_at = datetime.now(timezone.utc)
        job.scraped_at = None
        job.created_at = None

        result = await create_match_for_job(db, user, job, min_score=75.0)

        # Should return None when score is too low
        assert result is None

    @pytest.mark.asyncio
    @patch('app.services.matching.extract_job_requirements')
    async def test_create_match_database_error(self, mock_extract):
        """Test database error handling"""
        from app.services.matching import create_match_for_job

        mock_extract.return_value = {
            "required_skills": ["Python"],
            "nice_to_have_skills": []
        }

        db = MagicMock()
        # First query checks for rejected/hidden - return None (no prior rejection)
        # Second query checks for existing match - return None (new match)
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit.side_effect = Exception("Database error")

        user = MagicMock()
        user.id = 1
        user.skills = ["Python"]
        user.preferences = {"target_roles": ["Python Developer"]}
        user.experience_years = 5

        job = MagicMock()
        job.id = 1
        job.title = "Python Developer"
        job.company = "Test Co"
        job.description = "Python role"
        job.remote_type = "full"
        job.salary_min = 100000
        job.salary_max = 150000
        job.location = "Remote"
        job.eligible_regions = None
        job.visa_sponsorship = None
        job.posted_at = datetime.now(timezone.utc)
        job.scraped_at = None
        job.created_at = None

        result = await create_match_for_job(db, user, job)

        # Should return None and rollback on database error
        assert result is None
        db.rollback.assert_called_once()


class TestSkillClusters:
    """Test skill cluster semantic matching"""

    def test_calculate_skill_similarity_exact_match(self):
        """Test exact match returns 1.0"""
        assert calculate_skill_similarity("Python", "Python") == 1.0
        assert calculate_skill_similarity("python", "PYTHON") == 1.0

    def test_calculate_skill_similarity_related(self):
        """Test related skills return 0.5"""
        # Django and Flask are in same python_web cluster
        assert calculate_skill_similarity("Django", "Flask") == 0.5
        # React and Vue are in same javascript_frontend cluster
        assert calculate_skill_similarity("React", "Vue") == 0.5
        # PostgreSQL and MySQL are in same databases_sql cluster
        assert calculate_skill_similarity("PostgreSQL", "MySQL") == 0.5

    def test_calculate_skill_similarity_unrelated(self):
        """Test unrelated skills return 0.0"""
        # Python and React are not in any common cluster
        assert calculate_skill_similarity("CSS", "PostgreSQL") == 0.0

    def test_are_skills_related(self):
        """Test are_skills_related function"""
        # Same cluster
        assert are_skills_related("Docker", "Kubernetes") is True
        assert are_skills_related("Python", "Django") is True
        # Different cluster
        assert are_skills_related("React", "PostgreSQL") is False

    def test_get_related_skills(self):
        """Test getting related skills from clusters"""
        related = get_related_skills("Python")
        # Python is in multiple clusters: python_web, python_data, ml_tools, backend_languages
        assert "Django" in related
        assert "Flask" in related
        assert "FastAPI" in related
        assert "Pandas" in related
        assert "Python" not in related  # Should not include the skill itself


class TestDetectJobSeniority:
    """Test job seniority detection"""

    def test_detect_junior_from_title(self):
        """Test detecting junior level from title keywords"""
        assert detect_job_seniority("Junior Developer") == "junior"
        assert detect_job_seniority("Jr. Software Engineer") == "junior"
        assert detect_job_seniority("Entry Level Developer") == "junior"
        assert detect_job_seniority("Associate Software Engineer") == "junior"
        assert detect_job_seniority("Graduate Developer") == "junior"
        assert detect_job_seniority("Intern Software Developer") == "junior"

    def test_detect_senior_from_title(self):
        """Test detecting senior level from title keywords"""
        assert detect_job_seniority("Senior Developer") == "senior"
        assert detect_job_seniority("Sr. Software Engineer") == "senior"
        assert detect_job_seniority("Lead Engineer") == "senior"
        assert detect_job_seniority("Principal Software Engineer") == "senior"
        assert detect_job_seniority("Staff Engineer") == "senior"
        assert detect_job_seniority("Head of Engineering") == "senior"
        assert detect_job_seniority("Engineering Director") == "senior"

    def test_detect_mid_from_title(self):
        """Test detecting mid level from title without keywords"""
        assert detect_job_seniority("Software Engineer") == "mid"
        assert detect_job_seniority("Backend Developer") == "mid"
        assert detect_job_seniority("Full Stack Developer") == "mid"

    def test_detect_from_experience_years(self):
        """Test detecting seniority from experience requirements"""
        # Title has no keywords, fall back to experience
        assert detect_job_seniority("Developer", experience_min=1) == "junior"
        assert detect_job_seniority("Developer", experience_min=2) == "junior"
        assert detect_job_seniority("Developer", experience_min=5) == "senior"
        assert detect_job_seniority("Developer", experience_min=7) == "senior"

    def test_title_takes_precedence(self):
        """Test that title keywords take precedence over experience"""
        # Even with high experience req, Junior title = junior
        assert detect_job_seniority("Junior Developer", experience_min=5) == "junior"
        # Even with low experience req, Senior title = senior
        assert detect_job_seniority("Senior Developer", experience_min=1) == "senior"


class TestShouldMatchSeniority:
    """Test seniority filtering"""

    def test_no_seniority_filter(self):
        """Test when user has no seniority preference"""
        job = MagicMock()
        job.title = "Senior Developer"
        job_requirements = {"experience_years_min": 5}

        assert should_match_seniority({}, job, job_requirements) is True
        assert should_match_seniority({"seniority_filter": None}, job, job_requirements) is True

    def test_seniority_filter_matches(self):
        """Test when seniority filter matches job"""
        job = MagicMock()
        job.title = "Senior Software Engineer"
        job_requirements = {"experience_years_min": 5}

        assert should_match_seniority({"seniority_filter": "senior"}, job, job_requirements) is True

    def test_seniority_filter_mismatch(self):
        """Test when seniority filter doesn't match job"""
        job = MagicMock()
        job.title = "Junior Developer"
        job_requirements = {"experience_years_min": 0}

        # Senior looking at junior role
        assert should_match_seniority({"seniority_filter": "senior"}, job, job_requirements) is False

    def test_junior_filter(self):
        """Test junior seniority filter"""
        junior_job = MagicMock()
        junior_job.title = "Junior Developer"

        senior_job = MagicMock()
        senior_job.title = "Senior Developer"

        mid_job = MagicMock()
        mid_job.title = "Software Developer"

        prefs = {"seniority_filter": "junior"}

        assert should_match_seniority(prefs, junior_job, {}) is True
        assert should_match_seniority(prefs, senior_job, {}) is False
        assert should_match_seniority(prefs, mid_job, {}) is False


class TestCalculateFreshnessScore:
    """Test job freshness scoring"""

    def test_fresh_job_7_days(self):
        """Test jobs posted within 7 days get 100"""
        job = MagicMock()
        job.posted_at = datetime.now(timezone.utc) - timedelta(days=3)
        job.scraped_at = None
        job.created_at = None

        score = calculate_freshness_score(job)
        assert score == 100.0

    def test_job_7_to_14_days(self):
        """Test jobs 7-14 days old get 95"""
        job = MagicMock()
        job.posted_at = datetime.now(timezone.utc) - timedelta(days=10)
        job.scraped_at = None
        job.created_at = None

        score = calculate_freshness_score(job)
        assert score == 95.0

    def test_job_14_to_30_days(self):
        """Test jobs 14-30 days old get 85"""
        job = MagicMock()
        job.posted_at = datetime.now(timezone.utc) - timedelta(days=20)
        job.scraped_at = None
        job.created_at = None

        score = calculate_freshness_score(job)
        assert score == 85.0

    def test_job_over_30_days(self):
        """Test jobs over 30 days old get 70"""
        job = MagicMock()
        job.posted_at = datetime.now(timezone.utc) - timedelta(days=45)
        job.scraped_at = None
        job.created_at = None

        score = calculate_freshness_score(job)
        assert score == 70.0

    def test_falls_back_to_scraped_at(self):
        """Test falling back to scraped_at when posted_at is None"""
        job = MagicMock()
        job.posted_at = None
        job.scraped_at = datetime.now(timezone.utc) - timedelta(days=5)
        job.created_at = None

        score = calculate_freshness_score(job)
        assert score == 100.0

    def test_falls_back_to_created_at(self):
        """Test falling back to created_at when both dates are None"""
        job = MagicMock()
        job.posted_at = None
        job.scraped_at = None
        job.created_at = datetime.now(timezone.utc) - timedelta(days=25)

        score = calculate_freshness_score(job)
        assert score == 85.0

    def test_no_date_info(self):
        """Test when no date information is available"""
        job = MagicMock()
        job.posted_at = None
        job.scraped_at = None
        job.created_at = None

        score = calculate_freshness_score(job)
        assert score == 85.0  # Default moderate score


class TestFeedbackLoop:
    """Test user feedback loop (exclude rejected matches)"""

    @pytest.mark.asyncio
    @patch('app.services.matching.extract_job_requirements')
    async def test_skips_rejected_job(self, mock_extract):
        """Test that rejected jobs are skipped"""
        from app.services.matching import create_match_for_job
        from app.models import Match

        db = MagicMock()

        # Mock existing rejected match
        mock_rejected = MagicMock()
        mock_rejected.status = "rejected"
        db.query.return_value.filter.return_value.first.return_value = mock_rejected

        user = MagicMock()
        user.id = 1
        user.preferences = {}

        job = MagicMock()
        job.id = 100

        result = await create_match_for_job(db, user, job)

        # Should return None for rejected job
        assert result is None
        # LLM should NOT be called
        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.services.matching.extract_job_requirements')
    async def test_skips_hidden_job(self, mock_extract):
        """Test that hidden jobs are skipped"""
        from app.services.matching import create_match_for_job
        from app.models import Match

        db = MagicMock()

        # Mock existing hidden match
        mock_hidden = MagicMock()
        mock_hidden.status = "hidden"
        db.query.return_value.filter.return_value.first.return_value = mock_hidden

        user = MagicMock()
        user.id = 1
        user.preferences = {}

        job = MagicMock()
        job.id = 100

        result = await create_match_for_job(db, user, job)

        # Should return None for hidden job
        assert result is None
        # LLM should NOT be called
        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.services.matching.extract_job_requirements')
    async def test_skips_job_with_no_skills_extracted(self, mock_extract):
        """Test that jobs with no extracted skills are skipped"""
        from app.services.matching import create_match_for_job

        mock_extract.return_value = {
            "required_skills": [],  # No skills
            "nice_to_have_skills": []  # No skills
        }

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        user = MagicMock()
        user.id = 1
        user.skills = ["Python", "Django"]
        user.preferences = {}

        job = MagicMock()
        job.id = 100
        job.title = "Senior Research Engineer"
        job.company = "AI Institute"
        job.description = "Work on AI"
        job.remote_type = "full"
        job.eligible_regions = None
        job.visa_sponsorship = None

        result = await create_match_for_job(db, user, job)

        # Should return None - no skills extracted
        assert result is None

    @pytest.mark.asyncio
    @patch('app.services.matching.extract_job_requirements')
    async def test_skips_job_with_no_skill_overlap(self, mock_extract):
        """Test that jobs with zero skill overlap are skipped"""
        from app.services.matching import create_match_for_job

        # Use skills that are NOT in any shared cluster with user's skills
        mock_extract.return_value = {
            "required_skills": ["Figma", "Sketch", "Adobe XD"],  # Design tools
            "nice_to_have_skills": ["Illustrator"]
        }

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        user = MagicMock()
        user.id = 1
        user.skills = ["Python", "Django", "PostgreSQL"]  # Backend skills - no cluster overlap with design
        user.preferences = {"target_roles": ["Software Engineer"]}
        user.experience_years = 5

        job = MagicMock()
        job.id = 100
        job.title = "UI Designer"
        job.company = "Design Co"
        job.description = "Design work"
        job.remote_type = "full"
        job.salary_min = 100000
        job.salary_max = 150000
        job.location = "Remote"
        job.eligible_regions = None
        job.visa_sponsorship = None
        job.posted_at = datetime.now(timezone.utc)
        job.scraped_at = None
        job.created_at = None

        result = await create_match_for_job(db, user, job)

        # Should return None - no skill overlap (design vs backend)
        assert result is None

    @pytest.mark.asyncio
    async def test_match_user_with_all_jobs_excludes_rejected(self):
        """Test that match_user_with_all_jobs pre-filters rejected jobs"""
        from app.services.matching import match_user_with_all_jobs

        db = MagicMock()

        # First query: Match.job_id query for rejected jobs
        mock_rejected_subquery = MagicMock()
        mock_rejected_subquery.filter.return_value = mock_rejected_subquery
        mock_rejected_subquery.all.return_value = [(1,), (2,), (3,)]  # Jobs 1, 2, 3 are rejected

        # Second query: Job query
        mock_jobs_query = MagicMock()
        mock_jobs_query.order_by.return_value = mock_jobs_query
        mock_jobs_query.filter.return_value = mock_jobs_query
        mock_jobs_query.all.return_value = []  # No jobs to process

        # Set up query side effects based on call order
        db.query.side_effect = [mock_rejected_subquery, mock_jobs_query]

        user = MagicMock()
        user.id = 1
        user.preferences = {}
        user.skills = []

        result = await match_user_with_all_jobs(db, user)

        assert result == []
        # Verify that query was called twice (once for rejected, once for jobs)
        assert db.query.call_count == 2
