"""
User repository — database queries for user management.
Keeps all SQL logic in one place, separate from business logic.
"""

from sqlalchemy.orm import Session

from core.security import hash_password
from models.user import User, UserRole


def get_by_email(db: Session, email: str) -> User | None:
    """Find a user by email address (case-insensitive)."""
    return db.query(User).filter(User.email == email.lower()).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    """Find a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    *,
    email: str,
    name: str,
    password: str | None = None,
    oauth_provider: str | None = None,
    oauth_id: str | None = None,
    role: UserRole = UserRole.CUSTOMER,
    email_verified: bool = False,
) -> User:
    """Create a new user. Hashes the password if provided."""
    user = User(
        email=email.lower(),
        name=name,
        hashed_password=hash_password(password) if password else None,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        role=role,
        email_verified=email_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_email_verified(db: Session, user: User) -> User:
    """Mark a user's email as verified."""
    user.email_verified = True
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: User, new_password: str) -> User:
    """Update a user's password (hashes the new one)."""
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_oauth_user(
    db: Session,
    *,
    email: str,
    name: str,
    oauth_provider: str,
    oauth_id: str,
) -> User:
    """
    Find an existing user by email or create a new OAuth user.
    If the user exists but was created with email/password, link the OAuth account.
    """
    user = get_by_email(db, email)
    if user:
        # Link OAuth if not already linked
        if not user.oauth_provider:
            user.oauth_provider = oauth_provider
            user.oauth_id = oauth_id
        # OAuth users are auto-verified (email confirmed by provider)
        if not user.email_verified:
            user.email_verified = True
        db.commit()
        db.refresh(user)
        return user

    # Create new OAuth user — no password needed, email pre-verified
    return create_user(
        db,
        email=email,
        name=name,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        email_verified=True,
    )
