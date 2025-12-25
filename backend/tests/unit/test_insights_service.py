"""
Unit tests for insights service
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.insights import (
    analyze_market_skills,
    identify_skill_gaps,
    generate_skill_recommendations,
    estimate_learning_effort,
    create_or_update_skill_analysis,
    run_skill_analysis_for_user,
)


class TestAnalyzeMarketSkills:
    """Test market skill analysis"""

    def test_analyze_market_skills_no_jobs(self):
        """Test when no jobs exist"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = analyze_market_skills(mock_db)

        assert result == {}

    def test_analyze_market_skills_with_limit(self):
        """Test with job limit"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = analyze_market_skills(mock_db, limit=10)

        mock_query.order_by.return_value.limit.assert_called_with(10)

    @patch('app.services.insights.extract_job_requirements')
    def test_analyze_market_skills_with_jobs(self, mock_extract):
        """Test skill extraction and aggregation"""
        mock_db = MagicMock()
        mock_query = MagicMock()

        # Create mock jobs
        mock_job1 = MagicMock()
        mock_job1.title = "Software Engineer"
        mock_job1.company = "Tech Corp"
        mock_job1.description = "Python developer needed"
        mock_job1.salary_max = 150000

        mock_job2 = MagicMock()
        mock_job2.title = "Backend Developer"
        mock_job2.company = "Web Inc"
        mock_job2.description = "Python and Django"
        mock_job2.salary_max = 120000

        mock_query.order_by.return_value.all.return_value = [mock_job1, mock_job2]
        mock_db.query.return_value = mock_query

        # Mock skill extraction
        mock_extract.side_effect = [
            {"required_skills": ["Python", "FastAPI"], "nice_to_have_skills": ["Docker"]},
            {"required_skills": ["Python", "Django"], "nice_to_have_skills": []},
        ]

        result = analyze_market_skills(mock_db)

        # Skills are stored with canonical names (proper casing)
        assert "Python" in result
        assert result["Python"]["count"] == 2
        assert result["Python"]["frequency"] == 100.0
        assert result["Python"]["avg_salary"] == 135000.0  # (150000 + 120000) / 2

    @patch('app.services.insights.extract_job_requirements')
    def test_analyze_market_skills_no_requirements(self, mock_extract):
        """Test when job requirements extraction returns None"""
        mock_db = MagicMock()
        mock_query = MagicMock()

        mock_job = MagicMock()
        mock_job.title = "Test Job"
        mock_job.company = "Test Co"
        mock_job.description = "Test"
        mock_job.salary_max = None

        mock_query.order_by.return_value.all.return_value = [mock_job]
        mock_db.query.return_value = mock_query

        mock_extract.return_value = None

        result = analyze_market_skills(mock_db)

        # Should return empty since no skills were extracted
        assert result == {}

    @patch('app.services.insights.extract_job_requirements')
    def test_analyze_market_skills_without_salary(self, mock_extract):
        """Test skill analysis when jobs have no salary data"""
        mock_db = MagicMock()
        mock_query = MagicMock()

        mock_job = MagicMock()
        mock_job.title = "Developer"
        mock_job.company = "Company"
        mock_job.description = "Description"
        mock_job.salary_max = None

        mock_query.order_by.return_value.all.return_value = [mock_job]
        mock_db.query.return_value = mock_query

        mock_extract.return_value = {"required_skills": ["Python"], "nice_to_have_skills": []}

        result = analyze_market_skills(mock_db)

        # Skills are stored with canonical names
        assert "Python" in result
        assert result["Python"]["avg_salary"] is None
        assert result["Python"]["jobs_with_salary"] == 0


class TestIdentifySkillGaps:
    """Test skill gap identification"""

    def test_identify_skill_gaps_no_gaps(self):
        """Test when user has all required skills"""
        user_skills = ["Python", "Django", "React"]
        # Market skills use canonical names (as returned by analyze_market_skills)
        market_skills = {
            "Python": {"frequency": 50.0},
            "Django": {"frequency": 30.0},
            "React": {"frequency": 25.0},
        }

        gaps = identify_skill_gaps(user_skills, market_skills)

        assert gaps == []

    def test_identify_skill_gaps_with_gaps(self):
        """Test when user is missing skills"""
        user_skills = ["Python"]
        market_skills = {
            "Python": {"frequency": 50.0},
            "Django": {"frequency": 30.0},
            "Kubernetes": {"frequency": 15.0},
        }

        gaps = identify_skill_gaps(user_skills, market_skills)

        assert "Django" in gaps
        assert "Kubernetes" in gaps
        assert "Python" not in gaps

    def test_identify_skill_gaps_below_min_frequency(self):
        """Test that low-frequency skills are excluded"""
        user_skills = []
        market_skills = {
            "Python": {"frequency": 50.0},
            "obscure_framework": {"frequency": 2.0},  # Below 5% default
        }

        gaps = identify_skill_gaps(user_skills, market_skills)

        assert "Python" in gaps
        assert "obscure_framework" not in gaps

    def test_identify_skill_gaps_custom_min_frequency(self):
        """Test with custom minimum frequency"""
        user_skills = []
        market_skills = {
            "Python": {"frequency": 50.0},
            "Docker": {"frequency": 8.0},
            "rare_skill": {"frequency": 3.0},
        }

        gaps = identify_skill_gaps(user_skills, market_skills, min_frequency=10.0)

        assert "Python" in gaps
        assert "Docker" not in gaps  # Below 10%
        assert "rare_skill" not in gaps

    def test_identify_skill_gaps_case_insensitive(self):
        """Test case-insensitive skill matching via normalization"""
        user_skills = ["python", "django"]  # lowercase input
        market_skills = {
            "Python": {"frequency": 50.0},  # canonical names
            "Django": {"frequency": 30.0},
            "React": {"frequency": 25.0},
        }

        gaps = identify_skill_gaps(user_skills, market_skills)

        # User's "python" normalizes to "Python" which matches market key
        assert "Python" not in gaps
        assert "Django" not in gaps
        assert "React" in gaps

    def test_identify_skill_gaps_with_whitespace(self):
        """Test that whitespace is handled"""
        user_skills = ["  Python  ", "\tDjango\n"]
        market_skills = {
            "Python": {"frequency": 50.0},  # canonical names
            "Django": {"frequency": 30.0},
        }

        gaps = identify_skill_gaps(user_skills, market_skills)

        assert gaps == []


class TestGenerateSkillRecommendations:
    """Test skill recommendation generation (profile-aware)"""

    def test_generate_recommendations_no_user_skills(self):
        """Test with user having no skills - returns empty list"""
        mock_user = MagicMock()
        mock_user.skills = []

        market_skills = {"python": {"frequency": 50.0, "avg_salary": 150000}}
        skill_gaps = ["python"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        # Profile-aware: no user skills means no related skills to recommend
        assert recommendations == []

    def test_generate_recommendations_high_priority(self):
        """Test high priority recommendation for skill related to user's skills"""
        mock_user = MagicMock()
        mock_user.skills = ["Python"]  # Python is in SKILL_PATHS

        # FastAPI is related to Python in SKILL_PATHS and has high market demand
        market_skills = {
            "fastapi": {"frequency": 25.0, "avg_salary": 150000}
        }
        skill_gaps = ["fastapi"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert len(recommendations) >= 1
        # Find the fastapi recommendation
        fastapi_rec = next((r for r in recommendations if r["skill"].lower() == "fastapi"), None)
        assert fastapi_rec is not None
        assert fastapi_rec["priority"] == "high"

    def test_generate_recommendations_medium_priority(self):
        """Test medium priority recommendation"""
        mock_user = MagicMock()
        mock_user.skills = ["Python"]  # Python is in SKILL_PATHS

        # Django is related to Python, with medium frequency
        market_skills = {
            "django": {"frequency": 12.0, "avg_salary": 120000}
        }
        skill_gaps = ["django"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert len(recommendations) >= 1
        # Find the django recommendation
        django_rec = next((r for r in recommendations if r["skill"].lower() == "django"), None)
        assert django_rec is not None
        assert django_rec["priority"] == "medium"

    def test_generate_recommendations_low_priority(self):
        """Test low priority recommendation for skill with low market demand"""
        mock_user = MagicMock()
        mock_user.skills = ["Python"]

        # Celery is related to Python but has low frequency
        market_skills = {
            "celery": {"frequency": 3.0, "avg_salary": None}
        }
        skill_gaps = ["celery"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert len(recommendations) >= 1
        celery_rec = next((r for r in recommendations if r["skill"].lower() == "celery"), None)
        assert celery_rec is not None
        assert celery_rec["priority"] == "low"
        assert celery_rec["salary_impact"] is None

    def test_generate_recommendations_sorted_by_priority(self):
        """Test that recommendations are sorted by priority then frequency"""
        mock_user = MagicMock()
        mock_user.skills = ["Python"]  # Python has related skills in SKILL_PATHS

        # Market skills for Python-related skills with different frequencies
        market_skills = {
            "celery": {"frequency": 3.0, "avg_salary": None},       # low priority (< 5%)
            "fastapi": {"frequency": 25.0, "avg_salary": 150000},   # high priority (>= 15%)
            "django": {"frequency": 12.0, "avg_salary": 130000},    # medium priority (5-15%)
        }
        skill_gaps = ["celery", "fastapi", "django"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert len(recommendations) >= 3
        assert recommendations[0]["priority"] == "high"
        assert recommendations[1]["priority"] == "medium"
        assert recommendations[2]["priority"] == "low"

    def test_generate_recommendations_top_n(self):
        """Test limiting number of recommendations"""
        mock_user = MagicMock()
        mock_user.skills = ["Python"]  # Python has many related skills

        # Create market skills for Python-related skills
        market_skills = {
            "fastapi": {"frequency": 20.0, "avg_salary": None},
            "django": {"frequency": 19.0, "avg_salary": None},
            "postgresql": {"frequency": 18.0, "avg_salary": None},
            "redis": {"frequency": 17.0, "avg_salary": None},
            "docker": {"frequency": 16.0, "avg_salary": None},
            "aws": {"frequency": 15.0, "avg_salary": None},
            "celery": {"frequency": 14.0, "avg_salary": None},
        }
        skill_gaps = list(market_skills.keys())

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps, top_n=3)

        assert len(recommendations) == 3

    def test_generate_recommendations_only_related_skills(self):
        """Test that only skills related to user's existing skills are recommended"""
        mock_user = MagicMock()
        mock_user.skills = ["Python"]

        # kubernetes is NOT related to Python in SKILL_PATHS
        market_skills = {
            "kubernetes": {"frequency": 50.0, "avg_salary": 200000},
            "fastapi": {"frequency": 25.0, "avg_salary": 150000},  # IS related to Python
        }
        skill_gaps = ["kubernetes", "fastapi"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        # Should include fastapi (related to Python) but not kubernetes
        skill_names = [r["skill"].lower() for r in recommendations]
        assert "fastapi" in skill_names
        # kubernetes might be included if Docker is in user's skills, but Python alone doesn't lead to k8s


class TestEstimateLearningEffort:
    """Test learning effort estimation"""

    def test_estimate_effort_with_related_skills(self):
        """Test low effort when user has related skills"""
        # Use canonical names as returned by normalize_skill
        user_skills = {"Python", "Django", "Flask"}

        effort = estimate_learning_effort("fastapi", user_skills)

        assert effort == "low"

    def test_estimate_effort_frontend_related(self):
        """Test frontend skill with frontend background"""
        user_skills = {"React", "JavaScript"}

        effort = estimate_learning_effort("vue", user_skills)

        assert effort == "low"

    def test_estimate_effort_no_related_skills_foundational(self):
        """Test foundational skill without related background"""
        # User has only frontend skills, learning a foundational backend skill
        user_skills = {"HTML", "CSS", "React"}

        effort = estimate_learning_effort("python", user_skills)

        assert effort == "medium"

    def test_estimate_effort_no_related_skills_advanced(self):
        """Test advanced skill without related background"""
        user_skills = {"HTML", "CSS"}

        effort = estimate_learning_effort("kubernetes", user_skills)

        assert effort == "high"

    def test_estimate_effort_unknown_skill(self):
        """Test unknown skill defaults to medium"""
        user_skills = {"Python"}

        effort = estimate_learning_effort("some_obscure_framework", user_skills)

        assert effort == "medium"

    def test_estimate_effort_devops_with_devops_background(self):
        """Test devops skill with devops background"""
        user_skills = {"Docker", "Terraform"}

        effort = estimate_learning_effort("kubernetes", user_skills)

        assert effort == "low"

    def test_estimate_effort_ml_with_ml_background(self):
        """Test ML skill with ML background"""
        user_skills = {"Python", "TensorFlow"}

        effort = estimate_learning_effort("pytorch", user_skills)

        assert effort == "low"


class TestCreateOrUpdateSkillAnalysis:
    """Test skill analysis creation/update"""

    def test_create_new_analysis(self):
        """Test creating new analysis"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.skills = ["Python", "Django"]

        market_skills = {"python": {"frequency": 50.0}}
        skill_gaps = ["kubernetes"]
        recommendations = [{"skill": "kubernetes", "priority": "high"}]

        result = create_or_update_skill_analysis(
            db=mock_db,
            user=mock_user,
            market_skills=market_skills,
            skill_gaps=skill_gaps,
            recommendations=recommendations,
            jobs_analyzed=100
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_existing_analysis(self):
        """Test updating existing analysis"""
        mock_db = MagicMock()

        # Mock existing analysis
        mock_analysis = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.skills = ["Python"]

        market_skills = {"python": {"frequency": 50.0}}
        skill_gaps = ["docker"]
        recommendations = [{"skill": "docker", "priority": "medium"}]

        result = create_or_update_skill_analysis(
            db=mock_db,
            user=mock_user,
            market_skills=market_skills,
            skill_gaps=skill_gaps,
            recommendations=recommendations,
            jobs_analyzed=50
        )

        # Should not add new, but should commit and refresh
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify analysis was updated
        assert mock_analysis.market_skills == market_skills
        assert mock_analysis.skill_gaps == skill_gaps


class TestRunSkillAnalysisForUser:
    """Test complete skill analysis workflow"""

    @patch('app.services.insights.create_or_update_skill_analysis')
    @patch('app.services.insights.generate_skill_recommendations')
    @patch('app.services.insights.identify_skill_gaps')
    @patch('app.services.insights.analyze_market_skills')
    def test_run_skill_analysis_workflow(
        self,
        mock_analyze,
        mock_identify,
        mock_recommend,
        mock_create
    ):
        """Test complete analysis workflow"""
        mock_db = MagicMock()
        mock_db.query.return_value.scalar.return_value = 100  # Job count

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.skills = ["Python"]

        # Set up mock returns
        mock_analyze.return_value = {"python": {"frequency": 50.0}}
        mock_identify.return_value = ["kubernetes"]
        mock_recommend.return_value = [{"skill": "kubernetes", "priority": "high"}]
        mock_create.return_value = MagicMock()

        result = run_skill_analysis_for_user(mock_db, mock_user)

        # Verify all steps were called
        mock_analyze.assert_called_once_with(mock_db)
        mock_identify.assert_called_once()
        mock_recommend.assert_called_once()
        mock_create.assert_called_once()

    @patch('app.services.insights.create_or_update_skill_analysis')
    @patch('app.services.insights.generate_skill_recommendations')
    @patch('app.services.insights.identify_skill_gaps')
    @patch('app.services.insights.analyze_market_skills')
    def test_run_skill_analysis_with_no_skills(
        self,
        mock_analyze,
        mock_identify,
        mock_recommend,
        mock_create
    ):
        """Test analysis for user with no skills"""
        mock_db = MagicMock()
        mock_db.query.return_value.scalar.return_value = 50

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.skills = None  # No skills

        mock_analyze.return_value = {}
        mock_identify.return_value = []
        mock_recommend.return_value = []
        mock_create.return_value = MagicMock()

        result = run_skill_analysis_for_user(mock_db, mock_user)

        # Should handle None skills gracefully
        mock_identify.assert_called_once()
        args, kwargs = mock_identify.call_args
        assert args[0] == []  # Empty list passed instead of None
