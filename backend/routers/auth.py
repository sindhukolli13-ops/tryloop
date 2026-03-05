"""
Auth router — signup, login, token refresh, email verification,
password reset, Google OAuth, and current user profile.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    return auth_service.signup(db, name=body.name, email=body.email, password=body.password)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password."""
    return auth_service.login(db, email=body.email, password=body.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access + refresh token pair."""
    return auth_service.refresh_token(db, token=body.refresh_token)


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify a user's email address with the token from the verification email."""
    auth_service.verify_email(db, token=body.token)
    return {"message": "Email verified successfully"}


@router.post("/password-reset-request", response_model=MessageResponse)
def password_reset_request(body: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset email. Always returns 200 to prevent user enumeration."""
    auth_service.request_password_reset(db, email=body.email)
    return {"message": "If that email exists, a reset link has been sent"}


@router.post("/password-reset", response_model=MessageResponse)
def password_reset(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using a valid reset token."""
    auth_service.reset_password(db, token=body.token, new_password=body.new_password)
    return {"message": "Password reset successfully"}


@router.post("/google", response_model=TokenResponse)
def google_auth(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Exchange a Google OAuth ID token for backend JWT tokens."""
    return auth_service.google_oauth_login(db, id_token=body.id_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return current_user
