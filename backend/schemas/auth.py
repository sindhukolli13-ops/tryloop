"""
Pydantic schemas for authentication requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Request schemas ──

class SignupRequest(BaseModel):
    """New user registration."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Email + password login."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Exchange a refresh token for new tokens."""
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Verify email address with a token from the verification email."""
    token: str


class PasswordResetRequest(BaseModel):
    """Request a password reset email."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Set a new password using a reset token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class GoogleAuthRequest(BaseModel):
    """Exchange a Google OAuth ID token for backend JWT tokens."""
    id_token: str


# ── Response schemas ──

class TokenResponse(BaseModel):
    """JWT access + refresh tokens returned on login/signup."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile data."""
    id: int
    email: str
    name: str
    role: str
    email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response for operations that don't return data."""
    message: str
