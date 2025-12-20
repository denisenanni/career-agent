"""
Redis cache service for storing and retrieving LLM results and generated content

This service provides a centralized Redis caching layer to:
- Store expensive LLM API call results
- Cache cover letters and CV highlights
- Reduce Claude API costs by 70-90%
- Provide sub-50ms response times for cached content
"""
import json
import logging
from typing import Optional, Any
from datetime import timedelta
import redis
from redis.exceptions import RedisError
from app.config import settings

logger = logging.getLogger(__name__)

# Redis connection pool (reused across requests)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create Redis client with connection pool

    Returns:
        Redis client or None if connection fails
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        # Test connection
        _redis_client.ping()
        logger.info("Redis connection established successfully")
        return _redis_client

    except RedisError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        _redis_client = None
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        _redis_client = None
        return None


def cache_set(key: str, value: Any, ttl_seconds: Optional[int] = None, track_metrics: bool = True) -> bool:
    """
    Store a value in Redis cache with optional TTL

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl_seconds: Time-to-live in seconds (None = no expiration)
        track_metrics: Whether to track set metrics (default True)

    Returns:
        True if successful, False otherwise
    """
    client = get_redis_client()
    if client is None:
        logger.warning(f"Redis not available, skipping cache set for key: {key}")
        return False

    try:
        # Serialize value to JSON
        serialized = json.dumps(value)

        if ttl_seconds:
            client.setex(key, ttl_seconds, serialized)
        else:
            client.set(key, serialized)

        logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
        if track_metrics:
            track_cache_set(key)
        return True

    except (RedisError, TypeError, ValueError) as e:
        logger.error(f"Failed to set cache for key {key}: {e}")
        return False


def cache_get(key: str, track_metrics: bool = True) -> Optional[Any]:
    """
    Retrieve a value from Redis cache

    Args:
        key: Cache key
        track_metrics: Whether to track hit/miss metrics (default True)

    Returns:
        Cached value (deserialized from JSON) or None if not found/error
    """
    client = get_redis_client()
    if client is None:
        logger.debug(f"Redis not available, cache miss for key: {key}")
        return None

    try:
        serialized = client.get(key)

        if serialized is None:
            logger.debug(f"Cache miss: {key}")
            if track_metrics:
                track_cache_miss(key)
            return None

        # Deserialize from JSON
        value = json.loads(serialized)
        logger.debug(f"Cache hit: {key}")
        if track_metrics:
            track_cache_hit(key)
        return value

    except (RedisError, json.JSONDecodeError) as e:
        logger.error(f"Failed to get cache for key {key}: {e}")
        return None


def cache_delete(key: str) -> bool:
    """
    Delete a value from Redis cache

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    client = get_redis_client()
    if client is None:
        logger.warning(f"Redis not available, skipping cache delete for key: {key}")
        return False

    try:
        client.delete(key)
        logger.debug(f"Cache deleted: {key}")
        return True

    except RedisError as e:
        logger.error(f"Failed to delete cache for key {key}: {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a pattern

    Args:
        pattern: Redis key pattern (e.g., "cover_letter:123:*")

    Returns:
        Number of keys deleted
    """
    client = get_redis_client()
    if client is None:
        logger.warning(f"Redis not available, skipping pattern delete for: {pattern}")
        return 0

    try:
        keys = client.keys(pattern)
        if keys:
            deleted = client.delete(*keys)
            logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
            return deleted
        return 0

    except RedisError as e:
        logger.error(f"Failed to delete pattern {pattern}: {e}")
        return 0


def cache_exists(key: str) -> bool:
    """
    Check if a key exists in Redis cache

    Args:
        key: Cache key

    Returns:
        True if key exists, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False

    try:
        return client.exists(key) > 0
    except RedisError as e:
        logger.error(f"Failed to check existence for key {key}: {e}")
        return False


def cache_get_ttl(key: str) -> Optional[int]:
    """
    Get remaining TTL for a key in seconds

    Args:
        key: Cache key

    Returns:
        TTL in seconds, -1 if no expiration, -2 if key doesn't exist, None on error
    """
    client = get_redis_client()
    if client is None:
        return None

    try:
        return client.ttl(key)
    except RedisError as e:
        logger.error(f"Failed to get TTL for key {key}: {e}")
        return None


# Common TTL values (in seconds)
TTL_30_DAYS = 60 * 60 * 24 * 30  # 30 days for cover letters, CV highlights
TTL_7_DAYS = 60 * 60 * 24 * 7    # 7 days for job extraction
TTL_1_HOUR = 60 * 60              # 1 hour for temporary data
TTL_5_MINUTES = 60 * 5            # 5 minutes for very temporary data


# Cache key builders
def build_cv_parse_key(cv_hash: str) -> str:
    """Build cache key for CV parsing results"""
    return f"cv_parse:{cv_hash}"


def build_job_extract_key(job_id: int) -> str:
    """Build cache key for job requirement extraction"""
    return f"job_extract:{job_id}"


def build_cover_letter_key(user_id: int, job_id: int) -> str:
    """Build cache key for cover letter generation"""
    return f"cover_letter:{user_id}:{job_id}"


def build_cv_highlights_key(user_id: int, job_id: int) -> str:
    """Build cache key for CV highlights generation"""
    return f"cv_highlights:{user_id}:{job_id}"


def build_match_content_pattern(user_id: int, job_id: int) -> str:
    """Build pattern to match all generated content for a match"""
    return f"*:{user_id}:{job_id}"


# =============================================================================
# Cache Metrics & Monitoring
# =============================================================================

# Metrics keys in Redis
METRICS_PREFIX = "cache_metrics"
METRICS_HITS = f"{METRICS_PREFIX}:hits"
METRICS_MISSES = f"{METRICS_PREFIX}:misses"
METRICS_SETS = f"{METRICS_PREFIX}:sets"

# Cost estimates per LLM call (in USD)
COST_CV_PARSE = 0.01       # Claude Haiku for CV parsing
COST_JOB_EXTRACT = 0.005   # Claude Haiku for job extraction
COST_COVER_LETTER = 0.15   # Claude Sonnet for cover letters
COST_CV_HIGHLIGHTS = 0.01  # Claude Haiku for CV highlights


def _increment_metric(metric_key: str, category: str, amount: int = 1) -> None:
    """Increment a metric counter in Redis"""
    client = get_redis_client()
    if client is None:
        return

    try:
        # Use hash to track metrics by category
        client.hincrby(metric_key, category, amount)
    except RedisError as e:
        logger.debug(f"Failed to increment metric {metric_key}:{category}: {e}")


def track_cache_hit(key: str) -> None:
    """Track a cache hit for metrics"""
    # Determine category from key prefix
    if key.startswith("cover_letter:"):
        category = "cover_letter"
    elif key.startswith("cv_highlights:"):
        category = "cv_highlights"
    elif key.startswith("cv_parse:"):
        category = "cv_parse"
    elif key.startswith("job_extract"):
        category = "job_extract"
    else:
        category = "other"

    _increment_metric(METRICS_HITS, category)
    _increment_metric(METRICS_HITS, "total")


def track_cache_miss(key: str) -> None:
    """Track a cache miss for metrics"""
    if key.startswith("cover_letter:"):
        category = "cover_letter"
    elif key.startswith("cv_highlights:"):
        category = "cv_highlights"
    elif key.startswith("cv_parse:"):
        category = "cv_parse"
    elif key.startswith("job_extract"):
        category = "job_extract"
    else:
        category = "other"

    _increment_metric(METRICS_MISSES, category)
    _increment_metric(METRICS_MISSES, "total")


def track_cache_set(key: str) -> None:
    """Track a cache set for metrics"""
    if key.startswith("cover_letter:"):
        category = "cover_letter"
    elif key.startswith("cv_highlights:"):
        category = "cv_highlights"
    elif key.startswith("cv_parse:"):
        category = "cv_parse"
    elif key.startswith("job_extract"):
        category = "job_extract"
    else:
        category = "other"

    _increment_metric(METRICS_SETS, category)
    _increment_metric(METRICS_SETS, "total")


def get_cache_stats() -> dict:
    """
    Get comprehensive cache statistics

    Returns:
        Dictionary with cache metrics, hit rates, and cost savings
    """
    client = get_redis_client()
    if client is None:
        return {"error": "Redis not available", "available": False}

    try:
        # Get all metrics
        hits = client.hgetall(METRICS_HITS) or {}
        misses = client.hgetall(METRICS_MISSES) or {}
        sets = client.hgetall(METRICS_SETS) or {}

        # Convert to integers
        hits = {k: int(v) for k, v in hits.items()}
        misses = {k: int(v) for k, v in misses.items()}
        sets = {k: int(v) for k, v in sets.items()}

        # Calculate hit rates and cost savings per category
        categories = ["cover_letter", "cv_highlights", "cv_parse", "job_extract"]
        cost_map = {
            "cover_letter": COST_COVER_LETTER,
            "cv_highlights": COST_CV_HIGHLIGHTS,
            "cv_parse": COST_CV_PARSE,
            "job_extract": COST_JOB_EXTRACT,
        }

        breakdown = {}
        total_savings = 0.0

        for cat in categories:
            cat_hits = hits.get(cat, 0)
            cat_misses = misses.get(cat, 0)
            cat_total = cat_hits + cat_misses
            cat_rate = (cat_hits / cat_total * 100) if cat_total > 0 else 0
            cat_savings = cat_hits * cost_map.get(cat, 0)
            total_savings += cat_savings

            breakdown[cat] = {
                "hits": cat_hits,
                "misses": cat_misses,
                "total_requests": cat_total,
                "hit_rate_percent": round(cat_rate, 1),
                "cost_per_miss_usd": cost_map.get(cat, 0),
                "savings_usd": round(cat_savings, 2),
            }

        # Overall stats
        total_hits = hits.get("total", 0)
        total_misses = misses.get("total", 0)
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        # Get Redis info
        info = client.info("memory")
        memory_used = info.get("used_memory_human", "unknown")

        # Count keys by pattern
        key_counts = {
            "cover_letters": len(client.keys("cover_letter:*")),
            "cv_highlights": len(client.keys("cv_highlights:*")),
            "cv_parses": len(client.keys("cv_parse:*")),
            "job_extracts": len(client.keys("job_extract*")),
        }

        return {
            "available": True,
            "summary": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_requests": total_requests,
                "hit_rate_percent": round(overall_hit_rate, 1),
                "total_savings_usd": round(total_savings, 2),
            },
            "breakdown": breakdown,
            "storage": {
                "memory_used": memory_used,
                "key_counts": key_counts,
                "total_keys": sum(key_counts.values()),
            },
        }

    except RedisError as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"error": str(e), "available": False}


def reset_cache_metrics() -> bool:
    """Reset all cache metrics (for testing or fresh start)"""
    client = get_redis_client()
    if client is None:
        return False

    try:
        client.delete(METRICS_HITS, METRICS_MISSES, METRICS_SETS)
        logger.info("Cache metrics reset")
        return True
    except RedisError as e:
        logger.error(f"Failed to reset metrics: {e}")
        return False
