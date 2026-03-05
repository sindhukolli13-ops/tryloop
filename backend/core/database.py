"""
Database engine, session factory, and base model class.
All models inherit from Base defined here.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import settings

# Engine — connection pool to PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # verify connections before using them
    echo=(settings.APP_ENV == "development"),  # log SQL in dev only
)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db():
    """
    Dependency that yields a database session per request.
    Automatically closes the session when the request is done.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
