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
    """Test skill recommendation generation"""

    def test_generate_recommendations_empty_gaps(self):
        """Test with no skill gaps"""
        mock_user = MagicMock()
        mock_user.skills = ["Python", "Django"]

        recommendations = generate_skill_recommendations(mock_user, {}, [])

        assert recommendations == []

    def test_generate_recommendations_high_priority(self):
        """Test high priority recommendation for frequent skill"""
        mock_user = MagicMock()
        mock_user.skills = ["JavaScript"]

        market_skills = {
            "kubernetes": {"frequency": 25.0, "avg_salary": 150000}
        }
        skill_gaps = ["kubernetes"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert len(recommendations) == 1
        assert recommendations[0]["skill"] == "kubernetes"
        assert recommendations[0]["priority"] == "high"
        assert "25%" in recommendations[0]["reason"]

    def test_generate_recommendations_medium_priority(self):
        """Test medium priority recommendation"""
        mock_user = MagicMock()
        mock_user.skills = []

        market_skills = {
            "docker": {"frequency": 15.0, "avg_salary": 120000}
        }
        skill_gaps = ["docker"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == "medium"

    def test_generate_recommendations_low_priority(self):
        """Test low priority recommendation"""
        mock_user = MagicMock()
        mock_user.skills = []

        market_skills = {
            "rare_tool": {"frequency": 8.0, "avg_salary": None}
        }
        skill_gaps = ["rare_tool"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == "low"
        assert recommendations[0]["salary_impact"] is None

    def test_generate_recommendations_sorted_by_priority(self):
        """Test that recommendations are sorted by priority"""
        mock_user = MagicMock()
        mock_user.skills = []

        market_skills = {
            "low_skill": {"frequency": 6.0, "avg_salary": None},
            "high_skill": {"frequency": 25.0, "avg_salary": 150000},
            "medium_skill": {"frequency": 12.0, "avg_salary": 130000},
        }
        skill_gaps = ["low_skill", "high_skill", "medium_skill"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        assert recommendations[0]["priority"] == "high"
        assert recommendations[1]["priority"] == "medium"
        assert recommendations[2]["priority"] == "low"

    def test_generate_recommendations_top_n(self):
        """Test limiting number of recommendations"""
        mock_user = MagicMock()
        mock_user.skills = []

        market_skills = {f"skill_{i}": {"frequency": 20.0 - i, "avg_salary": None} for i in range(15)}
        skill_gaps = [f"skill_{i}" for i in range(15)]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps, top_n=5)

        assert len(recommendations) == 5

    def test_generate_recommendations_missing_skill_data(self):
        """Test handling of skill gap not in market data"""
        mock_user = MagicMock()
        mock_user.skills = []

        market_skills = {"python": {"frequency": 50.0, "avg_salary": None}}
        skill_gaps = ["python", "nonexistent_skill"]

        recommendations = generate_skill_recommendations(mock_user, market_skills, skill_gaps)

        # Should only include python, not nonexistent_skill
        assert len(recommendations) == 1
        assert recommendations[0]["skill"] == "python"


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
