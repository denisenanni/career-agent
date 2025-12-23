"""
Authentication dependencies for FastAPI endpoints
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
import threading

from app.database import get_db
from app.models.user import User
from app.utils.auth import decode_access_token

# HTTP Bearer token scheme
security = HTTPBearer()

# In-memory user cache with LRU eviction to prevent memory leaks
# Format: OrderedDict[user_id, (user_object, expiry_time)]
_user_cache: OrderedDict[int, Tuple[User, datetime]] = OrderedDict()
_cache_lock = threading.Lock()
_cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
_cache_max_size = 1000  # Maximum number of cached users


def _cleanup_expired_entries() -> None:
    """Remove expired entries from cache (must be called with lock held)"""
    now = datetime.now(timezone.utc)
    expired_keys = [
        user_id for user_id, (_, expiry) in _user_cache.items()
        if now >= expiry
    ]
    for user_id in expired_keys:
        del _user_cache[user_id]


def _get_cached_user(user_id: int) -> Optional[User]:
    """Get user from cache if not expired (LRU: moves to end on access)"""
    with _cache_lock:
        if user_id in _user_cache:
            user, expiry = _user_cache[user_id]
            if datetime.now(timezone.utc) < expiry:
                # Move to end (most recently used)
                _user_cache.move_to_end(user_id)
                return user
            else:
                # Remove expired entry
                del _user_cache[user_id]
    return None


def _cache_user(user: User) -> None:
    """Cache user with TTL and LRU eviction"""
    with _cache_lock:
        now = datetime.now(timezone.utc)
        expiry = now + _cache_ttl

        # If already cached, update and move to end
        if user.id in _user_cache:
            _user_cache[user.id] = (user, expiry)
            _user_cache.move_to_end(user.id)
            return

        # Periodically cleanup expired entries (every 100 inserts worth of space)
        if len(_user_cache) >= _cache_max_size:
            _cleanup_expired_entries()

        # If still at max size after cleanup, remove oldest (LRU eviction)
        while len(_user_cache) >= _cache_max_size:
            _user_cache.popitem(last=False)  # Remove oldest

        _user_cache[user.id] = (user, expiry)


def invalidate_user_cache(user_id: int) -> None:
    """
    Invalidate cached user data

    Call this after updating user profile or settings to ensure
    fresh data on next request.
    """
    with _cache_lock:
        if user_id in _user_cache:
            del _user_cache[user_id]


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # Extract user_id from token
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    # Try to get user from cache first (reduces DB load)
    # Skip caching in test environment to avoid stale data between tests
    from app.config import settings
    user = None
    if settings.rate_limit_enabled:  # rate_limit_enabled is false in tests
        user = _get_cached_user(user_id)

    if user is None:
        # Cache miss or caching disabled - get from database
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise credentials_exception

        # Cache the user for future requests (if caching is enabled)
        if settings.rate_limit_enabled:
            _cache_user(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user (convenience dependency)

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
