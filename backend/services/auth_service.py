"""
Auth service — business logic for signup, login, token refresh,
email verification, password reset, and Google OAuth.
Orchestrates repositories, security utilities, and email sending.
"""

import logging

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from core.redis import (
    is_refresh_token_valid,
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
)
from core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    create_verification_token,
    decode_refresh_token,
    decode_special_token,
    verify_password,
)
from repositories import user_repo
from services.email_service import send_password_reset_email, send_verification_email

logger = logging.getLogger(__name__)

# TTL for refresh tokens in Redis (must match JWT expiry)
REFRESH_TOKEN_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def _issue_tokens(user_id: int, role: str) -> dict:
    """Create access + refresh tokens and store refresh in Redis."""
    access_token = create_access_token(user_id, role)
    refresh_token, jti = create_refresh_token(user_id)
    store_refresh_token(user_id, jti, REFRESH_TOKEN_TTL)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def signup(db: Session, *, name: str, email: str, password: str) -> dict:
    """Register a new user with email/password. Sends verification email."""
    existing = user_repo.get_by_email(db, email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = user_repo.create_user(db, email=email, name=name, password=password)

    # Send verification email (non-blocking — failure is logged, not fatal)
    token = create_verification_token(user.id)
    send_verification_email(user.email, user.name, token)

    return _issue_tokens(user.id, user.role.value)


def login(db: Session, *, email: str, password: str) -> dict:
    """Authenticate with email/password. Returns tokens."""
    user = user_repo.get_by_email(db, email)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return _issue_tokens(user.id, user.role.value)


def refresh_token(db: Session, *, token: str) -> dict:
    """Exchange a valid refresh token for a new token pair (rotation)."""
    payload = decode_refresh_token(token)
    user_id = int(payload["sub"])
    jti = payload["jti"]

    # Verify the token hasn't been revoked
    if not is_refresh_token_valid(user_id, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or expired")

    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate: revoke old token, issue new pair
    revoke_refresh_token(user_id, jti)
    return _issue_tokens(user.id, user.role.value)


def verify_email(db: Session, *, token: str) -> None:
    """Verify a user's email address using a verification token."""
    payload = decode_special_token(token, "email_verification")
    user_id = int(payload["sub"])

    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.email_verified:
        return  # already verified — idempotent

    user_repo.set_email_verified(db, user)


def request_password_reset(db: Session, *, email: str) -> None:
    """
    Send a password reset email. Always returns success to prevent
    user enumeration — even if the email doesn't exist.
    """
    user = user_repo.get_by_email(db, email)
    if not user:
        return  # silently ignore — no user enumeration

    token = create_password_reset_token(user.id)
    send_password_reset_email(user.email, user.name, token)


def reset_password(db: Session, *, token: str, new_password: str) -> None:
    """Reset a user's password using a valid reset token."""
    payload = decode_special_token(token, "password_reset")
    user_id = int(payload["sub"])

    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_repo.update_password(db, user, new_password)

    # Revoke all existing refresh tokens (force re-login everywhere)
    revoke_all_user_tokens(user_id)


def google_oauth_login(db: Session, *, id_token: str) -> dict:
    """
    Verify a Google ID token, find or create the user, and return backend tokens.
    The frontend sends the ID token obtained from Google Sign-In.
    """
    # Verify the ID token with Google's tokeninfo endpoint
    try:
        response = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=10.0,
        )
        response.raise_for_status()
        google_data = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google ID token")

    # Validate the audience matches our client ID
    if google_data.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience mismatch")

    email = google_data.get("email")
    name = google_data.get("name", email)
    google_id = google_data.get("sub")

    if not email or not google_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incomplete Google profile")

    user = user_repo.get_or_create_oauth_user(
        db,
        email=email,
        name=name,
        oauth_provider="google",
        oauth_id=google_id,
    )

    return _issue_tokens(user.id, user.role.value)
