"""
Unit tests for Redis cache service

Tests basic cache operations, key builders, and TTL functionality
"""
import os
import pytest
import time
from app.services.redis_cache import (
    cache_set, cache_get, cache_delete, cache_exists, cache_get_ttl,
    cache_delete_pattern, get_redis_client,
    build_cv_parse_key, build_job_extract_key,
    build_cover_letter_key, build_cv_highlights_key,
    build_match_content_pattern,
    TTL_30_DAYS, TTL_7_DAYS, TTL_1_HOUR
)


# Skip tests that require actual Redis connection
def redis_available():
    """Check if Redis is available"""
    client = get_redis_client()
    return client is not None


requires_redis = pytest.mark.skipif(
    not redis_available(),
    reason="Requires Redis (connection not available)"
)


@requires_redis
class TestRedisCacheBasicOperations:
    """Test basic Redis cache operations"""

    def test_cache_set_and_get(self):
        """Test setting and getting a value from cache"""
        key = "test:basic:1"
        value = {"message": "Hello Redis!", "count": 42}

        # Set value
        success = cache_set(key, value, ttl_seconds=60)
        assert success is True

        # Get value
        retrieved = cache_get(key)
        assert retrieved == value

        # Cleanup
        cache_delete(key)

    def test_cache_get_nonexistent_key(self):
        """Test getting a non-existent key returns None"""
        result = cache_get("test:nonexistent:key:12345")
        assert result is None

    def test_cache_delete(self):
        """Test deleting a key from cache"""
        key = "test:delete:1"
        value = {"data": "to be deleted"}

        cache_set(key, value, ttl_seconds=60)
        assert cache_exists(key) is True

        cache_delete(key)
        assert cache_exists(key) is False

    def test_cache_exists(self):
        """Test checking if a key exists"""
        key = "test:exists:1"

        assert cache_exists(key) is False

        cache_set(key, {"data": "test"}, ttl_seconds=60)
        assert cache_exists(key) is True

        cache_delete(key)
        assert cache_exists(key) is False

    def test_cache_with_different_data_types(self):
        """Test caching different data types"""
        test_cases = [
            ("test:string", "simple string"),
            ("test:int", 12345),
            ("test:float", 123.45),
            ("test:bool", True),
            ("test:list", [1, 2, 3, "four"]),
            ("test:dict", {"nested": {"data": [1, 2, 3]}}),
            ("test:none", None),
        ]

        for key, value in test_cases:
            cache_set(key, value, ttl_seconds=60)
            retrieved = cache_get(key)
            assert retrieved == value
            cache_delete(key)


@requires_redis
class TestRedisCacheTTL:
    """Test TTL (Time To Live) functionality"""

    def test_cache_with_ttl(self):
        """Test that cached values expire after TTL"""
        key = "test:ttl:1"
        value = {"data": "expires soon"}

        # Set with 2-second TTL
        cache_set(key, value, ttl_seconds=2)
        assert cache_exists(key) is True

        # Wait for expiration
        time.sleep(3)

        # Key should be gone
        assert cache_exists(key) is False
        assert cache_get(key) is None

    def test_cache_get_ttl(self):
        """Test getting remaining TTL for a key"""
        key = "test:ttl:check:1"
        cache_set(key, {"data": "test"}, ttl_seconds=60)

        ttl = cache_get_ttl(key)
        assert ttl is not None
        assert 55 <= ttl <= 60  # Should be close to 60 seconds

        cache_delete(key)

    def test_cache_without_ttl(self):
        """Test caching without expiration"""
        key = "test:no:ttl:1"
        cache_set(key, {"data": "persistent"})

        ttl = cache_get_ttl(key)
        # -1 means no expiration set
        assert ttl == -1

        cache_delete(key)

    def test_predefined_ttl_constants(self):
        """Test that predefined TTL constants have correct values"""
        assert TTL_30_DAYS == 60 * 60 * 24 * 30
        assert TTL_7_DAYS == 60 * 60 * 24 * 7
        assert TTL_1_HOUR == 60 * 60


@requires_redis
class TestRedisCachePatternDelete:
    """Test pattern-based deletion"""

    def test_delete_pattern(self):
        """Test deleting keys matching a pattern"""
        # Create multiple keys with same pattern
        base_pattern = "test:pattern:delete"
        keys = [
            f"{base_pattern}:1",
            f"{base_pattern}:2",
            f"{base_pattern}:3",
        ]

        for key in keys:
            cache_set(key, {"data": key}, ttl_seconds=60)

        # Verify all keys exist
        for key in keys:
            assert cache_exists(key) is True

        # Delete all keys matching pattern
        deleted_count = cache_delete_pattern(f"{base_pattern}:*")
        assert deleted_count == 3

        # Verify all keys are gone
        for key in keys:
            assert cache_exists(key) is False

    def test_delete_pattern_no_matches(self):
        """Test deleting with pattern that matches nothing"""
        deleted_count = cache_delete_pattern("test:nonexistent:pattern:*")
        assert deleted_count == 0


class TestCacheKeyBuilders:
    """Test cache key builder functions"""

    def test_build_cv_parse_key(self):
        """Test CV parse cache key builder"""
        cv_hash = "abc123def456"
        key = build_cv_parse_key(cv_hash)
        assert key == f"cv_parse:{cv_hash}"

    def test_build_job_extract_key(self):
        """Test job extraction cache key builder"""
        job_id = 12345
        key = build_job_extract_key(job_id)
        assert key == f"job_extract:{job_id}"

    def test_build_cover_letter_key(self):
        """Test cover letter cache key builder"""
        user_id = 100
        job_id = 200
        key = build_cover_letter_key(user_id, job_id)
        assert key == f"cover_letter:{user_id}:{job_id}"

    def test_build_cv_highlights_key(self):
        """Test CV highlights cache key builder"""
        user_id = 300
        job_id = 400
        key = build_cv_highlights_key(user_id, job_id)
        assert key == f"cv_highlights:{user_id}:{job_id}"

    def test_build_match_content_pattern(self):
        """Test match content pattern builder"""
        user_id = 500
        job_id = 600
        pattern = build_match_content_pattern(user_id, job_id)
        assert pattern == f"*:{user_id}:{job_id}"


@requires_redis
class TestRedisCacheIntegration:
    """Integration tests for realistic cache usage patterns"""

    def test_cache_workflow_cv_parsing(self):
        """Test typical CV parsing cache workflow"""
        cv_hash = "test_cv_hash_12345"
        key = build_cv_parse_key(cv_hash)
        cv_data = {
            "name": "John Doe",
            "skills": ["Python", "FastAPI", "React"],
            "experience": [
                {"company": "Tech Corp", "title": "Engineer"}
            ]
        }

        # First call - cache miss
        cached = cache_get(key)
        assert cached is None

        # Store in cache
        cache_set(key, cv_data, ttl_seconds=TTL_30_DAYS)

        # Second call - cache hit
        cached = cache_get(key)
        assert cached == cv_data

        # Cleanup
        cache_delete(key)

    def test_cache_workflow_cover_letter(self):
        """Test typical cover letter cache workflow"""
        user_id = 123
        job_id = 456
        key = build_cover_letter_key(user_id, job_id)

        cover_letter_data = {
            "cover_letter": "Dear Hiring Manager,...",
            "generated_at": "2025-12-17T12:00:00"
        }

        # Store in cache
        cache_set(key, cover_letter_data, ttl_seconds=TTL_30_DAYS)

        # Retrieve from cache
        cached = cache_get(key)
        assert cached["cover_letter"] == cover_letter_data["cover_letter"]
        assert cached["generated_at"] == cover_letter_data["generated_at"]

        # Cleanup
        cache_delete(key)

    def test_invalidate_all_match_content(self):
        """Test invalidating all cached content for a match"""
        user_id = 789
        job_id = 101

        # Create multiple cache entries for this match
        cover_key = build_cover_letter_key(user_id, job_id)
        highlights_key = build_cv_highlights_key(user_id, job_id)

        cache_set(cover_key, {"data": "cover letter"}, ttl_seconds=60)
        cache_set(highlights_key, {"data": "highlights"}, ttl_seconds=60)

        # Verify both exist
        assert cache_exists(cover_key) is True
        assert cache_exists(highlights_key) is True

        # Invalidate all content for this match
        pattern = build_match_content_pattern(user_id, job_id)
        deleted = cache_delete_pattern(pattern)
        assert deleted >= 2  # Should delete at least the 2 keys we created

        # Verify both are gone
        assert cache_exists(cover_key) is False
        assert cache_exists(highlights_key) is False


@requires_redis
class TestRedisCacheErrorHandling:
    """Test error handling and edge cases"""

    def test_cache_with_empty_string_key(self):
        """Test caching with empty string as key"""
        # Redis allows empty string keys, but it's not recommended
        key = ""
        value = {"data": "test"}

        success = cache_set(key, value, ttl_seconds=60)
        # Should work but we want to document this behavior
        assert isinstance(success, bool)

        if success:
            cache_delete(key)

    def test_cache_very_large_value(self):
        """Test caching a large value"""
        key = "test:large:value"
        # Create a large nested structure
        large_value = {
            "data": ["item"] * 1000,
            "nested": {
                "level1": {
                    "level2": {
                        "items": [{"id": i, "data": f"data_{i}"} for i in range(100)]
                    }
                }
            }
        }

        success = cache_set(key, large_value, ttl_seconds=60)
        assert success is True

        retrieved = cache_get(key)
        assert retrieved == large_value

        cache_delete(key)


# ============================================================================
# Mocked unit tests (don't require real Redis connection)
# ============================================================================
from unittest.mock import patch, MagicMock
from redis.exceptions import RedisError
from app.services.redis_cache import get_redis_client, TTL_5_MINUTES
import app.services.redis_cache as redis_cache_module


@pytest.fixture
def reset_redis_client():
    """Reset the global Redis client before and after test"""
    original = redis_cache_module._redis_client
    redis_cache_module._redis_client = None
    yield
    redis_cache_module._redis_client = original


class TestGetRedisClientMocked:
    """Test Redis client connection with mocks"""

    def test_get_redis_client_success(self, reset_redis_client):
        """Test successful Redis connection"""
        with patch('app.services.redis_cache.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client

            client = get_redis_client()

            assert client == mock_client
            mock_client.ping.assert_called_once()

    def test_get_redis_client_returns_cached_client(self, reset_redis_client):
        """Test that client is reused after first connection"""
        mock_client = MagicMock()
        redis_cache_module._redis_client = mock_client

        client = get_redis_client()

        assert client == mock_client

    def test_get_redis_client_redis_error(self, reset_redis_client):
        """Test Redis connection failure"""
        with patch('app.services.redis_cache.redis') as mock_redis:
            mock_redis.from_url.side_effect = RedisError("Connection failed")

            client = get_redis_client()

            assert client is None

    def test_get_redis_client_unexpected_error(self, reset_redis_client):
        """Test unexpected error during connection"""
        with patch('app.services.redis_cache.redis') as mock_redis:
            mock_redis.from_url.side_effect = Exception("Unexpected error")

            client = get_redis_client()

            assert client is None


class TestCacheSetMocked:
    """Test cache_set function with mocks"""

    def test_cache_set_with_ttl(self, reset_redis_client):
        """Test setting cache with TTL"""
        mock_client = MagicMock()
        redis_cache_module._redis_client = mock_client

        result = cache_set("test_key", {"data": "value"}, ttl_seconds=3600)

        assert result is True
        mock_client.setex.assert_called_once()

    def test_cache_set_without_ttl(self, reset_redis_client):
        """Test setting cache without TTL"""
        mock_client = MagicMock()
        redis_cache_module._redis_client = mock_client

        result = cache_set("test_key", {"data": "value"})

        assert result is True
        mock_client.set.assert_called_once()

    def test_cache_set_no_redis_client(self, reset_redis_client):
        """Test cache_set when Redis is unavailable"""
        with patch('app.services.redis_cache.get_redis_client', return_value=None):
            result = cache_set("test_key", {"data": "value"})

        assert result is False

    def test_cache_set_redis_error(self, reset_redis_client):
        """Test cache_set with Redis error"""
        mock_client = MagicMock()
        mock_client.set.side_effect = RedisError("Set failed")
        redis_cache_module._redis_client = mock_client

        result = cache_set("test_key", {"data": "value"})

        assert result is False

    def test_cache_set_serialization_error(self, reset_redis_client):
        """Test cache_set with non-serializable value"""
        mock_client = MagicMock()
        redis_cache_module._redis_client = mock_client

        # Create a non-serializable object
        class NonSerializable:
            pass

        result = cache_set("test_key", NonSerializable())

        assert result is False


class TestCacheGetMocked:
    """Test cache_get function with mocks"""

    def test_cache_get_hit(self, reset_redis_client):
        """Test cache hit"""
        mock_client = MagicMock()
        mock_client.get.return_value = '{"data": "value"}'
        redis_cache_module._redis_client = mock_client

        result = cache_get("test_key")

        assert result == {"data": "value"}

    def test_cache_get_miss(self, reset_redis_client):
        """Test cache miss"""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        redis_cache_module._redis_client = mock_client

        result = cache_get("test_key")

        assert result is None

    def test_cache_get_no_redis_client(self, reset_redis_client):
        """Test cache_get when Redis is unavailable"""
        with patch('app.services.redis_cache.get_redis_client', return_value=None):
            result = cache_get("test_key")

        assert result is None

    def test_cache_get_redis_error(self, reset_redis_client):
        """Test cache_get with Redis error"""
        mock_client = MagicMock()
        mock_client.get.side_effect = RedisError("Get failed")
        redis_cache_module._redis_client = mock_client

        result = cache_get("test_key")

        assert result is None

    def test_cache_get_json_decode_error(self, reset_redis_client):
        """Test cache_get with invalid JSON"""
        mock_client = MagicMock()
        mock_client.get.return_value = "invalid json {"
        redis_cache_module._redis_client = mock_client

        result = cache_get("test_key")

        assert result is None


class TestCacheDeleteMocked:
    """Test cache_delete function with mocks"""

    def test_cache_delete_success(self, reset_redis_client):
        """Test successful cache deletion"""
        mock_client = MagicMock()
        redis_cache_module._redis_client = mock_client

        result = cache_delete("test_key")

        assert result is True
        mock_client.delete.assert_called_once_with("test_key")

    def test_cache_delete_no_redis_client(self, reset_redis_client):
        """Test cache_delete when Redis is unavailable"""
        with patch('app.services.redis_cache.get_redis_client', return_value=None):
            result = cache_delete("test_key")

        assert result is False

    def test_cache_delete_redis_error(self, reset_redis_client):
        """Test cache_delete with Redis error"""
        mock_client = MagicMock()
        mock_client.delete.side_effect = RedisError("Delete failed")
        redis_cache_module._redis_client = mock_client

        result = cache_delete("test_key")

        assert result is False


class TestCacheDeletePatternMocked:
    """Test cache_delete_pattern function with mocks"""

    def test_cache_delete_pattern_with_keys(self, reset_redis_client):
        """Test deleting keys by pattern"""
        mock_client = MagicMock()
        mock_client.keys.return_value = ["key1", "key2", "key3"]
        mock_client.delete.return_value = 3
        redis_cache_module._redis_client = mock_client

        result = cache_delete_pattern("test:*")

        assert result == 3
        mock_client.delete.assert_called_once_with("key1", "key2", "key3")

    def test_cache_delete_pattern_no_keys(self, reset_redis_client):
        """Test deleting pattern with no matching keys"""
        mock_client = MagicMock()
        mock_client.keys.return_value = []
        redis_cache_module._redis_client = mock_client

        result = cache_delete_pattern("test:*")

        assert result == 0
        mock_client.delete.assert_not_called()

    def test_cache_delete_pattern_no_redis_client(self, reset_redis_client):
        """Test cache_delete_pattern when Redis is unavailable"""
        with patch('app.services.redis_cache.get_redis_client', return_value=None):
            result = cache_delete_pattern("test:*")

        assert result == 0

    def test_cache_delete_pattern_redis_error(self, reset_redis_client):
        """Test cache_delete_pattern with Redis error"""
        mock_client = MagicMock()
        mock_client.keys.side_effect = RedisError("Keys failed")
        redis_cache_module._redis_client = mock_client

        result = cache_delete_pattern("test:*")

        assert result == 0


class TestCacheExistsMocked:
    """Test cache_exists function with mocks"""

    def test_cache_exists_true(self, reset_redis_client):
        """Test when key exists"""
        mock_client = MagicMock()
        mock_client.exists.return_value = 1
        redis_cache_module._redis_client = mock_client

        result = cache_exists("test_key")

        assert result is True

    def test_cache_exists_false(self, reset_redis_client):
        """Test when key doesn't exist"""
        mock_client = MagicMock()
        mock_client.exists.return_value = 0
        redis_cache_module._redis_client = mock_client

        result = cache_exists("test_key")

        assert result is False

    def test_cache_exists_no_redis_client(self, reset_redis_client):
        """Test cache_exists when Redis is unavailable"""
        with patch('app.services.redis_cache.get_redis_client', return_value=None):
            result = cache_exists("test_key")

        assert result is False

    def test_cache_exists_redis_error(self, reset_redis_client):
        """Test cache_exists with Redis error"""
        mock_client = MagicMock()
        mock_client.exists.side_effect = RedisError("Exists failed")
        redis_cache_module._redis_client = mock_client

        result = cache_exists("test_key")

        assert result is False


class TestCacheGetTtlMocked:
    """Test cache_get_ttl function with mocks"""

    def test_cache_get_ttl_with_ttl(self, reset_redis_client):
        """Test getting TTL for key with expiration"""
        mock_client = MagicMock()
        mock_client.ttl.return_value = 3600
        redis_cache_module._redis_client = mock_client

        result = cache_get_ttl("test_key")

        assert result == 3600

    def test_cache_get_ttl_no_expiration(self, reset_redis_client):
        """Test getting TTL for key without expiration"""
        mock_client = MagicMock()
        mock_client.ttl.return_value = -1
        redis_cache_module._redis_client = mock_client

        result = cache_get_ttl("test_key")

        assert result == -1

    def test_cache_get_ttl_key_not_exists(self, reset_redis_client):
        """Test getting TTL for non-existent key"""
        mock_client = MagicMock()
        mock_client.ttl.return_value = -2
        redis_cache_module._redis_client = mock_client

        result = cache_get_ttl("test_key")

        assert result == -2

    def test_cache_get_ttl_no_redis_client(self, reset_redis_client):
        """Test cache_get_ttl when Redis is unavailable"""
        with patch('app.services.redis_cache.get_redis_client', return_value=None):
            result = cache_get_ttl("test_key")

        assert result is None

    def test_cache_get_ttl_redis_error(self, reset_redis_client):
        """Test cache_get_ttl with Redis error"""
        mock_client = MagicMock()
        mock_client.ttl.side_effect = RedisError("TTL failed")
        redis_cache_module._redis_client = mock_client

        result = cache_get_ttl("test_key")

        assert result is None


class TestTtlConstantsMocked:
    """Test TTL constant values"""

    def test_ttl_5_minutes(self):
        """Test 5 minutes TTL value"""
        assert TTL_5_MINUTES == 60 * 5
