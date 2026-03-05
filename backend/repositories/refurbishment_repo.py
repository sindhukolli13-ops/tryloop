"""
Refurbishment log repository — database queries for refurbishment tracking.
"""

from sqlalchemy.orm import Session

from models.refurbishment_log import RefurbishmentLog, RefurbStatus, ReturnCondition


def get_by_id(db: Session, log_id: int) -> RefurbishmentLog | None:
    return db.query(RefurbishmentLog).filter(RefurbishmentLog.id == log_id).first()


def get_for_trial(db: Session, trial_id: int) -> RefurbishmentLog | None:
    """Get the refurbishment log for a specific trial (usually one per trial)."""
    return (
        db.query(RefurbishmentLog)
        .filter(RefurbishmentLog.trial_id == trial_id)
        .first()
    )


def get_for_unit(db: Session, device_unit_id: int) -> list[RefurbishmentLog]:
    """Get all refurbishment history for a device unit."""
    return (
        db.query(RefurbishmentLog)
        .filter(RefurbishmentLog.device_unit_id == device_unit_id)
        .order_by(RefurbishmentLog.created_at.desc())
        .all()
    )


def get_all(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[RefurbishmentLog], int]:
    """Admin: list all refurbishment logs with optional status filter."""
    query = db.query(RefurbishmentLog)
    if status:
        query = query.filter(RefurbishmentLog.status == RefurbStatus(status))
    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(RefurbishmentLog.created_at.desc()).offset(offset).limit(page_size).all()
    return logs, total


def create(db: Session, *, data: dict) -> RefurbishmentLog:
    """Create a new refurbishment log entry."""
    if "condition_on_return" in data and isinstance(data["condition_on_return"], str):
        data["condition_on_return"] = ReturnCondition(data["condition_on_return"])
    if "status" in data and isinstance(data["status"], str):
        data["status"] = RefurbStatus(data["status"])

    log = RefurbishmentLog(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update(db: Session, log: RefurbishmentLog, *, data: dict) -> RefurbishmentLog:
    """Update a refurbishment log."""
    for key, value in data.items():
        if value is not None:
            if key == "status" and isinstance(value, str):
                value = RefurbStatus(value)
            elif key == "condition_on_return" and isinstance(value, str):
                value = ReturnCondition(value)
            setattr(log, key, value)
    db.commit()
    db.refresh(log)
    return log
