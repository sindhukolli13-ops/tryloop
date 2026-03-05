"""
Device service — business logic for the device catalog and inventory.
Orchestrates device and device unit repositories.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories import device_repo, device_unit_repo
from schemas.device import (
    DeviceCompareResponse,
    DeviceCreate,
    DeviceListResponse,
    DeviceResponse,
    DeviceUnitCreate,
    DeviceUnitListResponse,
    DeviceUnitResponse,
    DeviceUnitUpdate,
    DeviceUpdate,
)

logger = logging.getLogger(__name__)


# ── Helpers ──

def _device_to_response(db: Session, device) -> DeviceResponse:
    """Convert a Device ORM object to a DeviceResponse with availability count."""
    available_units = device_repo.get_available_unit_count(db, device.id)
    return DeviceResponse(
        id=device.id,
        name=device.name,
        brand=device.brand,
        category=device.category,
        description=device.description,
        specs=device.specs,
        images=device.images,
        trial_price_7d=float(device.trial_price_7d),
        trial_price_14d=float(device.trial_price_14d),
        purchase_price=float(device.purchase_price),
        deposit_amount=float(device.deposit_amount),
        is_featured=device.is_featured,
        is_active=device.is_active,
        available_units=available_units,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


def _unit_to_response(unit) -> DeviceUnitResponse:
    """Convert a DeviceUnit ORM object to a DeviceUnitResponse."""
    return DeviceUnitResponse(
        id=unit.id,
        device_id=unit.device_id,
        serial_number=unit.serial_number,
        condition_grade=unit.condition_grade.value,
        status=unit.status.value,
        rental_count=unit.rental_count,
        total_lifecycle_revenue=float(unit.total_lifecycle_revenue),
        created_at=unit.created_at,
        updated_at=unit.updated_at,
    )


# ── Device catalog (public + admin) ──

def list_devices(
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
) -> DeviceListResponse:
    """List devices with filtering and pagination (customer-facing)."""
    devices, total = device_repo.get_all(
        db,
        page=page,
        page_size=page_size,
        category=category,
        brand=brand,
        search=search,
        min_price=min_price,
        max_price=max_price,
        is_featured=is_featured,
        available_only=available_only,
    )
    items = [_device_to_response(db, d) for d in devices]
    return DeviceListResponse(items=items, total=total, page=page, page_size=page_size)


def get_device(db: Session, device_id: int) -> DeviceResponse:
    """Get a single device by ID. Raises 404 if not found or inactive."""
    device = device_repo.get_by_id(db, device_id)
    if not device or not device.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return _device_to_response(db, device)


def get_featured_devices(db: Session, limit: int = 6) -> list[DeviceResponse]:
    """Get featured devices for the homepage."""
    devices = device_repo.get_featured(db, limit=limit)
    return [_device_to_response(db, d) for d in devices]


def compare_devices(db: Session, device_ids: list[int]) -> DeviceCompareResponse:
    """Compare up to 3 devices side by side."""
    if len(device_ids) < 2 or len(device_ids) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comparison requires 2 or 3 device IDs",
        )
    devices = device_repo.get_multiple_by_ids(db, device_ids)
    if len(devices) != len(device_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more devices not found",
        )
    items = [_device_to_response(db, d) for d in devices]
    return DeviceCompareResponse(devices=items)


def get_filter_options(db: Session) -> dict:
    """Get available categories and brands for filter dropdowns."""
    return {
        "categories": device_repo.get_categories(db),
        "brands": device_repo.get_brands(db),
    }


# ── Device admin CRUD ──

def create_device(db: Session, data: DeviceCreate) -> DeviceResponse:
    """Admin: add a new device to the catalog."""
    device = device_repo.create(db, data=data.model_dump())
    logger.info("Device created: id=%d name=%s", device.id, device.name)
    return _device_to_response(db, device)


def update_device(db: Session, device_id: int, data: DeviceUpdate) -> DeviceResponse:
    """Admin: update an existing device."""
    device = device_repo.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    # Only include fields that were explicitly set (not None)
    update_data = data.model_dump(exclude_unset=True)
    device = device_repo.update(db, device, data=update_data)
    logger.info("Device updated: id=%d", device.id)
    return _device_to_response(db, device)


def delete_device(db: Session, device_id: int) -> None:
    """Admin: soft-delete a device (marks as inactive)."""
    device = device_repo.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    device_repo.delete(db, device)
    logger.info("Device soft-deleted: id=%d", device.id)


# ── Device unit management ──

def list_units(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    device_id: int | None = None,
    unit_status: str | None = None,
    condition_grade: str | None = None,
) -> DeviceUnitListResponse:
    """Admin: list device units with filtering and pagination."""
    units, total = device_unit_repo.get_all(
        db,
        page=page,
        page_size=page_size,
        device_id=device_id,
        status=unit_status,
        condition_grade=condition_grade,
    )
    items = [_unit_to_response(u) for u in units]
    return DeviceUnitListResponse(items=items, total=total, page=page, page_size=page_size)


def get_unit(db: Session, unit_id: int) -> DeviceUnitResponse:
    """Admin: get a single device unit by ID."""
    unit = device_unit_repo.get_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device unit not found")
    return _unit_to_response(unit)


def create_unit(db: Session, data: DeviceUnitCreate) -> DeviceUnitResponse:
    """Admin: register a new physical unit in inventory."""
    # Verify the parent device exists
    device = device_repo.get_by_id(db, data.device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    # Check for duplicate serial number
    existing = device_unit_repo.get_by_serial_number(db, data.serial_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Serial number already registered",
        )

    unit = device_unit_repo.create(db, data=data.model_dump())
    logger.info("Device unit created: id=%d serial=%s", unit.id, unit.serial_number)
    return _unit_to_response(unit)


def update_unit(db: Session, unit_id: int, data: DeviceUnitUpdate) -> DeviceUnitResponse:
    """Admin: update a device unit (condition, status, serial number)."""
    unit = device_unit_repo.get_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device unit not found")

    # If changing serial number, check for duplicates
    if data.serial_number and data.serial_number != unit.serial_number:
        existing = device_unit_repo.get_by_serial_number(db, data.serial_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Serial number already registered",
            )

    update_data = data.model_dump(exclude_unset=True)
    unit = device_unit_repo.update(db, unit, data=update_data)
    logger.info("Device unit updated: id=%d", unit.id)
    return _unit_to_response(unit)


def delete_unit(db: Session, unit_id: int) -> None:
    """Admin: delete a device unit (only if it has no trial history)."""
    unit = device_unit_repo.get_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device unit not found")

    # Prevent deletion if the unit has been used in trials
    if unit.rental_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete unit with trial history. Consider retiring it instead.",
        )

    device_unit_repo.delete(db, unit)
    logger.info("Device unit deleted: id=%d", unit.id)


def get_unit_status_counts(db: Session, device_id: int) -> dict[str, int]:
    """Admin: get unit counts grouped by status for a device."""
    return device_unit_repo.count_by_status(db, device_id)
