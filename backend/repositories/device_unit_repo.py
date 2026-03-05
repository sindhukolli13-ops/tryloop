"""
Device unit repository — database queries for physical inventory units.
Each unit has a serial number, condition grade, and lifecycle status.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.device_unit import ConditionGrade, DeviceUnit, UnitStatus


def get_by_id(db: Session, unit_id: int) -> DeviceUnit | None:
    """Find a device unit by primary key."""
    return db.query(DeviceUnit).filter(DeviceUnit.id == unit_id).first()


def get_by_serial_number(db: Session, serial_number: str) -> DeviceUnit | None:
    """Find a device unit by its unique serial number."""
    return db.query(DeviceUnit).filter(DeviceUnit.serial_number == serial_number).first()


def get_all(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    device_id: int | None = None,
    status: str | None = None,
    condition_grade: str | None = None,
) -> tuple[list[DeviceUnit], int]:
    """
    Retrieve device units with optional filtering and pagination.
    Returns (units, total_count) tuple.
    """
    query = db.query(DeviceUnit)

    if device_id is not None:
        query = query.filter(DeviceUnit.device_id == device_id)

    if status:
        query = query.filter(DeviceUnit.status == UnitStatus(status))

    if condition_grade:
        query = query.filter(DeviceUnit.condition_grade == ConditionGrade(condition_grade))

    total = query.count()

    offset = (page - 1) * page_size
    units = query.order_by(DeviceUnit.created_at.desc()).offset(offset).limit(page_size).all()

    return units, total


def get_available_for_device(db: Session, device_id: int) -> list[DeviceUnit]:
    """Get all available units for a specific device (for trial booking)."""
    return (
        db.query(DeviceUnit)
        .filter(DeviceUnit.device_id == device_id, DeviceUnit.status == UnitStatus.AVAILABLE)
        .all()
    )


def count_by_status(db: Session, device_id: int) -> dict[str, int]:
    """Count units grouped by status for a given device (for inventory overview)."""
    rows = (
        db.query(DeviceUnit.status, func.count(DeviceUnit.id))
        .filter(DeviceUnit.device_id == device_id)
        .group_by(DeviceUnit.status)
        .all()
    )
    return {row[0].value: row[1] for row in rows}


def create(db: Session, *, data: dict) -> DeviceUnit:
    """Register a new physical unit in inventory."""
    # Convert string values to enum members
    if "condition_grade" in data and isinstance(data["condition_grade"], str):
        data["condition_grade"] = ConditionGrade(data["condition_grade"])

    unit = DeviceUnit(**data)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update(db: Session, unit: DeviceUnit, *, data: dict) -> DeviceUnit:
    """Update a device unit. Only sets fields that are not None."""
    for key, value in data.items():
        if value is not None:
            # Convert string enum values to their enum type
            if key == "condition_grade" and isinstance(value, str):
                value = ConditionGrade(value)
            elif key == "status" and isinstance(value, str):
                value = UnitStatus(value)
            setattr(unit, key, value)
    db.commit()
    db.refresh(unit)
    return unit


def delete(db: Session, unit: DeviceUnit) -> None:
    """Hard-delete a device unit (only allowed if unit has no trial history)."""
    db.delete(unit)
    db.commit()
