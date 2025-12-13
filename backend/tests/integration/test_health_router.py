"""
Integration tests for Health Router
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test GET /health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "career-agent-api"

    def test_root_endpoint(self, client):
        """Test GET / root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Career Agent API"
        assert data["docs"] == "/docs"
