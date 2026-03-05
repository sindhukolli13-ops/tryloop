"""
Device repository — database queries for the device product catalog.
Handles CRUD, filtering, search, and featured device retrieval.
"""

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models.device import Device
from models.device_unit import DeviceUnit, UnitStatus


def get_available_unit_count(db: Session, device_id: int) -> int:
    """Count units with 'available' status for a given device."""
    return (
        db.query(func.count(DeviceUnit.id))
        .filter(DeviceUnit.device_id == device_id, DeviceUnit.status == UnitStatus.AVAILABLE)
        .scalar()
    ) or 0


def get_by_id(db: Session, device_id: int) -> Device | None:
    """Find a device by primary key."""
    return db.query(Device).filter(Device.id == device_id).first()


def get_all(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    brand: str | None = None,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    is_featured: bool | None = None,
    available_only: bool = False,
    active_only: bool = True,
) -> tuple[list[Device], int]:
    """
    Retrieve devices with optional filtering and pagination.
    Returns (devices, total_count) tuple for pagination support.
    """
    query = db.query(Device)

    # Only show active devices by default (soft-delete filter)
    if active_only:
        query = query.filter(Device.is_active == True)  # noqa: E712

    if category:
        query = query.filter(Device.category == category)

    if brand:
        query = query.filter(Device.brand == brand)

    if is_featured is not None:
        query = query.filter(Device.is_featured == is_featured)

    # Text search across name, brand, and description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Device.name.ilike(search_term),
                Device.brand.ilike(search_term),
                Device.description.ilike(search_term),
            )
        )

    # Price filtering uses the 7-day trial price as the reference
    if min_price is not None:
        query = query.filter(Device.trial_price_7d >= min_price)

    if max_price is not None:
        query = query.filter(Device.trial_price_7d <= max_price)

    # Filter to only devices that have at least one available unit
    if available_only:
        available_device_ids = (
            db.query(DeviceUnit.device_id)
            .filter(DeviceUnit.status == UnitStatus.AVAILABLE)
            .distinct()
            .subquery()
        )
        query = query.filter(Device.id.in_(available_device_ids))

    total = query.count()

    # Paginate (default sort: newest first)
    offset = (page - 1) * page_size
    devices = query.order_by(Device.created_at.desc()).offset(offset).limit(page_size).all()

    return devices, total


def get_featured(db: Session, limit: int = 6) -> list[Device]:
    """Get featured devices for the homepage."""
    return (
        db.query(Device)
        .filter(Device.is_featured == True, Device.is_active == True)  # noqa: E712
        .order_by(Device.updated_at.desc())
        .limit(limit)
        .all()
    )


def get_categories(db: Session) -> list[str]:
    """Get all distinct device categories (for filter dropdowns)."""
    rows = db.query(Device.category).filter(Device.is_active == True).distinct().all()  # noqa: E712
    return [row[0] for row in rows]


def get_brands(db: Session) -> list[str]:
    """Get all distinct brands (for filter dropdowns)."""
    rows = db.query(Device.brand).filter(Device.is_active == True).distinct().all()  # noqa: E712
    return [row[0] for row in rows]


def create(db: Session, *, data: dict) -> Device:
    """Create a new device in the catalog."""
    device = Device(**data)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update(db: Session, device: Device, *, data: dict) -> Device:
    """Update an existing device. Only sets fields that are not None."""
    for key, value in data.items():
        if value is not None:
            setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device


def delete(db: Session, device: Device) -> None:
    """Soft-delete a device by marking it inactive."""
    device.is_active = False
    db.commit()


def get_multiple_by_ids(db: Session, device_ids: list[int]) -> list[Device]:
    """Retrieve multiple devices by their IDs (for comparison feature)."""
    return (
        db.query(Device)
        .filter(Device.id.in_(device_ids), Device.is_active == True)  # noqa: E712
        .all()
    )
