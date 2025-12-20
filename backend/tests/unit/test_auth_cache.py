"""
Unit tests for JWT user caching optimization
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from app.dependencies.auth import (
    _get_cached_user,
    _cache_user,
    invalidate_user_cache,
    _user_cache,
    _cache_lock
)
from app.models.user import User


@pytest.fixture
def sample_user():
    """Create a sample user object"""
    user = Mock(spec=User)
    user.id = 42
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    return user


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear user cache before each test"""
    with _cache_lock:
        _user_cache.clear()
    yield
    with _cache_lock:
        _user_cache.clear()


class TestUserCaching:
    """Test user caching functionality"""

    def test_cache_user_and_get(self, sample_user):
        """Test caching a user and retrieving it"""
        # Cache the user
        _cache_user(sample_user)

        # Retrieve from cache
        cached_user = _get_cached_user(sample_user.id)

        assert cached_user is not None
        assert cached_user.id == sample_user.id
        assert cached_user.email == sample_user.email

    def test_get_cached_user_miss(self):
        """Test cache miss returns None"""
        cached_user = _get_cached_user(999)
        assert cached_user is None

    def test_cache_expiry(self, sample_user):
        """Test that cached users expire after TTL"""
        # Cache the user
        _cache_user(sample_user)

        # Manually expire the cache entry
        with _cache_lock:
            user_obj, _ = _user_cache[sample_user.id]
            expired_time = datetime.now(timezone.utc) - timedelta(seconds=1)
            _user_cache[sample_user.id] = (user_obj, expired_time)

        # Should return None and remove expired entry
        cached_user = _get_cached_user(sample_user.id)
        assert cached_user is None

        # Verify entry was removed
        with _cache_lock:
            assert sample_user.id not in _user_cache

    def test_invalidate_user_cache(self, sample_user):
        """Test cache invalidation"""
        # Cache the user
        _cache_user(sample_user)

        # Verify it's cached
        assert _get_cached_user(sample_user.id) is not None

        # Invalidate
        invalidate_user_cache(sample_user.id)

        # Should no longer be cached
        assert _get_cached_user(sample_user.id) is None

    def test_invalidate_nonexistent_cache(self):
        """Test invalidating a non-existent cache entry doesn't error"""
        # Should not raise an error
        invalidate_user_cache(999)

    def test_cache_overwrites_existing(self, sample_user):
        """Test that caching same user twice overwrites"""
        # Cache the user
        _cache_user(sample_user)

        # Modify user and cache again
        sample_user.full_name = "Updated Name"
        _cache_user(sample_user)

        # Should get the updated version
        cached_user = _get_cached_user(sample_user.id)
        assert cached_user.full_name == "Updated Name"

    def test_cache_multiple_users(self, sample_user):
        """Test caching multiple users simultaneously"""
        # Create multiple users
        user1 = sample_user
        user2 = Mock(spec=User)
        user2.id = 43
        user2.email = "user2@example.com"
        user2.is_active = True

        user3 = Mock(spec=User)
        user3.id = 44
        user3.email = "user3@example.com"
        user3.is_active = True

        # Cache all users
        _cache_user(user1)
        _cache_user(user2)
        _cache_user(user3)

        # All should be retrievable
        assert _get_cached_user(user1.id).id == 42
        assert _get_cached_user(user2.id).id == 43
        assert _get_cached_user(user3.id).id == 44

        # Invalidate one
        invalidate_user_cache(user2.id)

        # Others should still be cached
        assert _get_cached_user(user1.id) is not None
        assert _get_cached_user(user2.id) is None
        assert _get_cached_user(user3.id) is not None


class TestAuthDependencyWithCache:
    """Test get_current_user dependency with caching"""

    @patch('app.dependencies.auth.decode_access_token')
    def test_get_current_user_cache_hit(self, mock_decode, sample_user):
        """Test that get_current_user uses cache when caching enabled"""
        from app.dependencies.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from app.config import settings

        # Store original value and enable caching
        original_rate_limit = settings.rate_limit_enabled
        settings.rate_limit_enabled = True

        try:
            # Setup mocks
            mock_decode.return_value = {"user_id": sample_user.id}
            mock_db = Mock()

            # Pre-cache the user
            _cache_user(sample_user)

            # Call get_current_user
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="fake_token"
            )

            result = get_current_user(credentials, mock_db)

            # Should return the cached user
            assert result.id == sample_user.id

            # Database should NOT be queried
            mock_db.query.assert_not_called()
        finally:
            # Restore original value
            settings.rate_limit_enabled = original_rate_limit

    @patch('app.dependencies.auth.decode_access_token')
    def test_get_current_user_cache_miss_queries_db(self, mock_decode, sample_user):
        """Test that get_current_user queries DB on cache miss"""
        from app.dependencies.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from app.config import settings

        # Store original value and enable caching
        original_rate_limit = settings.rate_limit_enabled
        settings.rate_limit_enabled = True

        try:
            # Setup mocks
            mock_decode.return_value = {"user_id": sample_user.id}
            mock_db = Mock()
            mock_query = Mock()
            mock_filter = Mock()

            # Setup query chain
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_filter
            mock_filter.first.return_value = sample_user

            # Ensure cache is empty
            invalidate_user_cache(sample_user.id)

            # Call get_current_user
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="fake_token"
            )

            result = get_current_user(credentials, mock_db)

            # Should query database
            mock_db.query.assert_called_once()

            # Should return the user
            assert result.id == sample_user.id

            # Should now be cached for next request
            cached_user = _get_cached_user(sample_user.id)
            assert cached_user is not None
            assert cached_user.id == sample_user.id
        finally:
            # Restore original value
            settings.rate_limit_enabled = original_rate_limit


class TestCacheConcurrency:
    """Test thread safety of cache operations"""

    def test_cache_is_thread_safe(self, sample_user):
        """Test that cache operations use locks properly"""
        import threading
        import time

        results = []
        errors = []

        def cache_and_retrieve():
            try:
                for i in range(10):
                    _cache_user(sample_user)
                    time.sleep(0.001)  # Small delay to encourage race conditions
                    cached = _get_cached_user(sample_user.id)
                    if cached is not None:
                        results.append(cached.id)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = [threading.Thread(target=cache_and_retrieve) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should not have any errors
        assert len(errors) == 0

        # All results should be correct
        assert all(r == sample_user.id for r in results)
