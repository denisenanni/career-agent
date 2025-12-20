"""
Integration tests for Insights Router
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.skill_analysis import SkillAnalysis


@pytest.fixture
def user_with_skills(db_session: Session, test_user):
    """Ensure test user has skills"""
    test_user.skills = ["Python", "FastAPI", "React"]
    db_session.commit()
    db_session.refresh(test_user)
    return test_user


@pytest.fixture
def skill_analysis(db_session: Session, user_with_skills):
    """Create a skill analysis for the user"""
    analysis = SkillAnalysis(
        user_id=user_with_skills.id,
        analysis_date=datetime.now(timezone.utc),
        market_skills={
            "python": {"count": 100, "frequency": 50.0, "avg_salary": 150000, "jobs_with_salary": 80},
            "kubernetes": {"count": 40, "frequency": 20.0, "avg_salary": 160000, "jobs_with_salary": 30},
        },
        user_skills=["Python", "FastAPI", "React"],
        skill_gaps=["kubernetes", "docker"],
        recommendations=[
            {
                "skill": "kubernetes",
                "priority": "high",
                "reason": "Required in 20% of jobs, avg salary $160,000",
                "frequency": 20.0,
                "salary_impact": 160000,
                "learning_effort": "medium"
            },
            {
                "skill": "docker",
                "priority": "high",
                "reason": "Required in 25% of jobs",
                "frequency": 25.0,
                "salary_impact": None,
                "learning_effort": "low"
            },
        ],
        jobs_analyzed=200
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


class TestGetSkillInsights:
    """Test GET /api/insights/skills endpoint"""

    def test_get_skill_insights_no_skills(self, authenticated_client, test_user, db_session):
        """Test getting insights when user has no skills"""
        # Ensure user has no skills
        test_user.skills = []
        db_session.commit()

        response = authenticated_client.get("/api/insights/skills")

        assert response.status_code == 400
        assert "add skills" in response.json()["detail"].lower()

    def test_get_skill_insights_with_cached_analysis(
        self, authenticated_client, user_with_skills, skill_analysis
    ):
        """Test getting insights when analysis is cached"""
        response = authenticated_client.get("/api/insights/skills")

        assert response.status_code == 200
        data = response.json()

        assert "user_skills" in data
        assert "skill_gaps" in data
        assert "recommendations" in data
        assert "market_skills" in data
        assert "jobs_analyzed" in data
        assert data["jobs_analyzed"] == 200
        assert len(data["recommendations"]) == 2

    @patch('app.routers.insights.run_skill_analysis_for_user')
    def test_get_skill_insights_no_cached_analysis(
        self, mock_run_analysis, authenticated_client, user_with_skills, db_session
    ):
        """Test getting insights when no cached analysis exists"""
        mock_analysis = MagicMock()
        mock_analysis.user_skills = ["Python", "FastAPI"]
        mock_analysis.skill_gaps = ["kubernetes"]
        mock_analysis.recommendations = [{
            "skill": "kubernetes",
            "priority": "high",
            "reason": "High demand",
            "frequency": 20.0,
            "salary_impact": 160000,
            "learning_effort": "medium"
        }]
        mock_analysis.market_skills = {}
        mock_analysis.jobs_analyzed = 100
        mock_analysis.analysis_date = datetime.now(timezone.utc)
        mock_run_analysis.return_value = mock_analysis

        response = authenticated_client.get("/api/insights/skills")

        assert response.status_code == 200
        mock_run_analysis.assert_called_once()

    @patch('app.routers.insights.run_skill_analysis_for_user')
    def test_get_skill_insights_refresh(
        self, mock_run_analysis, authenticated_client, user_with_skills, skill_analysis
    ):
        """Test refreshing insights with refresh=true"""
        mock_analysis = MagicMock()
        mock_analysis.user_skills = ["Python"]
        mock_analysis.skill_gaps = ["kubernetes"]
        mock_analysis.recommendations = []
        mock_analysis.market_skills = {}
        mock_analysis.jobs_analyzed = 50
        mock_analysis.analysis_date = datetime.now(timezone.utc)
        mock_run_analysis.return_value = mock_analysis

        response = authenticated_client.get("/api/insights/skills?refresh=true")

        assert response.status_code == 200
        mock_run_analysis.assert_called_once()

    @patch('app.routers.insights.run_skill_analysis_for_user')
    def test_get_skill_insights_error(
        self, mock_run_analysis, authenticated_client, user_with_skills
    ):
        """Test error handling during insight generation"""
        mock_run_analysis.side_effect = Exception("Analysis failed")

        response = authenticated_client.get("/api/insights/skills")

        assert response.status_code == 500
        assert "Failed to get skill insights" in response.json()["detail"]


class TestRefreshSkillInsights:
    """Test POST /api/insights/skills/refresh endpoint"""

    def test_refresh_skill_insights_no_skills(self, authenticated_client, test_user, db_session):
        """Test refreshing insights when user has no skills"""
        test_user.skills = []
        db_session.commit()

        response = authenticated_client.post("/api/insights/skills/refresh")

        assert response.status_code == 400
        assert "add skills" in response.json()["detail"].lower()

    @patch('app.routers.insights.run_skill_analysis_for_user')
    def test_refresh_skill_insights_success(
        self, mock_run_analysis, authenticated_client, user_with_skills
    ):
        """Test successfully refreshing insights"""
        mock_analysis = MagicMock()
        mock_analysis.user_skills = ["Python", "FastAPI"]
        mock_analysis.skill_gaps = ["kubernetes", "docker"]
        mock_analysis.recommendations = [{
            "skill": "kubernetes",
            "priority": "high",
            "reason": "High demand",
            "frequency": 20.0,
            "salary_impact": 160000,
            "learning_effort": "medium"
        }]
        mock_analysis.market_skills = {"kubernetes": {"frequency": 20.0}}
        mock_analysis.jobs_analyzed = 150
        mock_analysis.analysis_date = datetime.now(timezone.utc)
        mock_run_analysis.return_value = mock_analysis

        response = authenticated_client.post("/api/insights/skills/refresh")

        assert response.status_code == 200
        data = response.json()

        assert data["jobs_analyzed"] == 150
        mock_run_analysis.assert_called_once()

    @patch('app.routers.insights.run_skill_analysis_for_user')
    def test_refresh_skill_insights_error(
        self, mock_run_analysis, authenticated_client, user_with_skills
    ):
        """Test error handling during refresh"""
        mock_run_analysis.side_effect = Exception("Refresh failed")

        response = authenticated_client.post("/api/insights/skills/refresh")

        assert response.status_code == 500
        assert "Failed to refresh skill insights" in response.json()["detail"]
