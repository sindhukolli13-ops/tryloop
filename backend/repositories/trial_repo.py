"""
Trial repository — database queries for trial lifecycle management.
"""

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.trial import Trial, TrialStatus


def get_by_id(db: Session, trial_id: int) -> Trial | None:
    return db.query(Trial).filter(Trial.id == trial_id).first()


def get_by_stripe_session(db: Session, stripe_payment_intent_id: str) -> Trial | None:
    """Find a trial by its Stripe payment intent ID."""
    return (
        db.query(Trial)
        .filter(Trial.stripe_payment_intent_id == stripe_payment_intent_id)
        .first()
    )


def get_user_trials(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[Trial], int]:
    """Get all trials for a specific customer, with optional status filter."""
    query = db.query(Trial).filter(Trial.user_id == user_id)

    if status:
        query = query.filter(Trial.status == TrialStatus(status))

    total = query.count()
    offset = (page - 1) * page_size
    trials = query.order_by(Trial.created_at.desc()).offset(offset).limit(page_size).all()
    return trials, total


def get_all(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    user_id: int | None = None,
    device_id: int | None = None,
    overdue_only: bool = False,
) -> tuple[list[Trial], int]:
    """Admin: list all trials with optional filtering."""
    query = db.query(Trial)

    if status:
        query = query.filter(Trial.status == TrialStatus(status))
    if user_id:
        query = query.filter(Trial.user_id == user_id)
    if device_id:
        query = query.filter(Trial.device_id == device_id)
    if overdue_only:
        # Overdue = status is still ACTIVE but end_date has passed
        query = query.filter(
            Trial.status == TrialStatus.ACTIVE,
            Trial.end_date < date.today(),
        )

    total = query.count()
    offset = (page - 1) * page_size
    trials = query.order_by(Trial.created_at.desc()).offset(offset).limit(page_size).all()
    return trials, total


def create(db: Session, *, data: dict) -> Trial:
    """Create a new trial record."""
    trial = Trial(**data)
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial


def update_status(db: Session, trial: Trial, new_status: TrialStatus) -> Trial:
    """Update only the status field of a trial."""
    trial.status = new_status
    db.commit()
    db.refresh(trial)
    return trial


def update(db: Session, trial: Trial, *, data: dict) -> Trial:
    """Update multiple fields on a trial."""
    for key, value in data.items():
        if value is not None:
            setattr(trial, key, value)
    db.commit()
    db.refresh(trial)
    return trial


def count_active_for_unit(db: Session, device_unit_id: int) -> int:
    """Check if a device unit currently has an active (non-terminal) trial.
    Used to prevent double-booking at the application level."""
    active_statuses = [
        TrialStatus.RESERVED,
        TrialStatus.SHIPPED,
        TrialStatus.ACTIVE,
    ]
    return (
        db.query(func.count(Trial.id))
        .filter(
            Trial.device_unit_id == device_unit_id,
            Trial.status.in_(active_statuses),
        )
        .scalar()
    ) or 0
