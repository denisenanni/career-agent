"""
Authentication dependencies for FastAPI endpoints
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
import threading

from app.database import get_db
from app.models.user import User
from app.utils.auth import decode_access_token

# HTTP Bearer token scheme
security = HTTPBearer()

# In-memory user cache to reduce DB lookups
# Format: {user_id: (user_object, expiry_time)}
_user_cache: Dict[int, tuple[User, datetime]] = {}
_cache_lock = threading.Lock()
_cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes


def _get_cached_user(user_id: int) -> Optional[User]:
    """Get user from cache if not expired"""
    with _cache_lock:
        if user_id in _user_cache:
            user, expiry = _user_cache[user_id]
            if datetime.now(timezone.utc) < expiry:
                return user
            else:
                # Remove expired entry
                del _user_cache[user_id]
    return None


def _cache_user(user: User) -> None:
    """Cache user with TTL"""
    with _cache_lock:
        expiry = datetime.now(timezone.utc) + _cache_ttl
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
