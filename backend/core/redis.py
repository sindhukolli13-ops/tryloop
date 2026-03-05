"""
Redis client singleton for refresh token storage, session caching, etc.
Uses the REDIS_URL from application settings.
"""

import redis

from core.config import settings

# Synchronous Redis client — sufficient for FastAPI with sync endpoints
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def store_refresh_token(user_id: int, jti: str, ttl_seconds: int) -> None:
    """Store a refresh token identifier in Redis with expiry."""
    key = f"refresh:{user_id}:{jti}"
    redis_client.setex(key, ttl_seconds, "valid")


def is_refresh_token_valid(user_id: int, jti: str) -> bool:
    """Check if a refresh token is still valid (not revoked or expired)."""
    key = f"refresh:{user_id}:{jti}"
    return redis_client.get(key) == "valid"


def revoke_refresh_token(user_id: int, jti: str) -> None:
    """Revoke a single refresh token."""
    key = f"refresh:{user_id}:{jti}"
    redis_client.delete(key)


def revoke_all_user_tokens(user_id: int) -> None:
    """Revoke all refresh tokens for a user (e.g. on password change)."""
    pattern = f"refresh:{user_id}:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
