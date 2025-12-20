"""
Integration tests for Admin Cache Monitoring endpoints
"""
import pytest
from unittest.mock import patch


class TestCacheStatsEndpoint:
    """Test GET /api/admin/cache/stats endpoint"""

    def test_cache_stats_requires_auth(self, client):
        """Test that unauthenticated users cannot access cache stats"""
        response = client.get("/api/admin/cache/stats")
        # Returns 403 (either not authenticated or not admin)
        assert response.status_code in [401, 403]

    def test_cache_stats_requires_admin(self, authenticated_client):
        """Test that non-admin users cannot access cache stats"""
        response = authenticated_client.get("/api/admin/cache/stats")
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_cache_stats_returns_data_for_admin(self, admin_client):
        """Test that admin can access cache stats"""
        mock_stats = {
            "available": True,
            "summary": {
                "total_hits": 100,
                "total_misses": 20,
                "total_requests": 120,
                "hit_rate_percent": 83.3,
                "total_savings_usd": 12.50,
            },
            "breakdown": {
                "cover_letter": {"hits": 50, "misses": 5, "savings_usd": 7.50},
                "cv_highlights": {"hits": 30, "misses": 10, "savings_usd": 0.30},
            },
            "storage": {
                "memory_used": "1.5M",
                "key_counts": {"cover_letters": 50, "cv_highlights": 30},
                "total_keys": 80,
            },
        }

        with patch("app.routers.admin.get_cache_stats", return_value=mock_stats):
            response = admin_client.get("/api/admin/cache/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert "summary" in data
        assert data["summary"]["total_hits"] == 100

    def test_cache_stats_handles_redis_unavailable(self, admin_client):
        """Test response when Redis is not available"""
        mock_stats = {
            "available": False,
            "error": "Redis not available"
        }

        with patch("app.routers.admin.get_cache_stats", return_value=mock_stats):
            response = admin_client.get("/api/admin/cache/stats")

        assert response.status_code == 503
        assert "Redis not available" in response.json()["detail"]


class TestCacheResetMetricsEndpoint:
    """Test POST /api/admin/cache/reset-metrics endpoint"""

    def test_reset_metrics_requires_auth(self, client):
        """Test that unauthenticated users cannot reset metrics"""
        response = client.post("/api/admin/cache/reset-metrics")
        # Returns 403 (either not authenticated or not admin)
        assert response.status_code in [401, 403]

    def test_reset_metrics_requires_admin(self, authenticated_client):
        """Test that non-admin users cannot reset metrics"""
        response = authenticated_client.post("/api/admin/cache/reset-metrics")
        assert response.status_code == 403

    def test_reset_metrics_succeeds_for_admin(self, admin_client):
        """Test that admin can reset cache metrics"""
        with patch("app.routers.admin.reset_cache_metrics", return_value=True):
            response = admin_client.post("/api/admin/cache/reset-metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache metrics reset successfully"

    def test_reset_metrics_handles_redis_unavailable(self, admin_client):
        """Test response when Redis is not available for reset"""
        with patch("app.routers.admin.reset_cache_metrics", return_value=False):
            response = admin_client.post("/api/admin/cache/reset-metrics")

        assert response.status_code == 503
        assert "Redis not available" in response.json()["detail"]
