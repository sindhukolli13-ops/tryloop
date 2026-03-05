"""
Inventory router — admin-only management of physical device units.
Covers CRUD for units, status tracking, and condition grades.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_role
from models.user import User, UserRole
from schemas.auth import MessageResponse
from schemas.device import (
    DeviceUnitCreate,
    DeviceUnitListResponse,
    DeviceUnitResponse,
    DeviceUnitUpdate,
)
from services import device_service

# All inventory endpoints require admin or staff role
admin_dep = Depends(require_role([UserRole.ADMIN, UserRole.STAFF]))

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/units", response_model=DeviceUnitListResponse)
def list_units(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    device_id: int | None = None,
    status: str | None = None,
    condition_grade: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = admin_dep,
):
    """Admin: list all device units with optional filtering."""
    return device_service.list_units(
        db,
        page=page,
        page_size=page_size,
        device_id=device_id,
        unit_status=status,
        condition_grade=condition_grade,
    )


@router.get("/units/{unit_id}", response_model=DeviceUnitResponse)
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = admin_dep,
):
    """Admin: get details for a single device unit."""
    return device_service.get_unit(db, unit_id)


@router.post("/units", response_model=DeviceUnitResponse, status_code=201)
def create_unit(
    body: DeviceUnitCreate,
    db: Session = Depends(get_db),
    current_user: User = admin_dep,
):
    """Admin: register a new physical unit in inventory."""
    return device_service.create_unit(db, body)


@router.patch("/units/{unit_id}", response_model=DeviceUnitResponse)
def update_unit(
    unit_id: int,
    body: DeviceUnitUpdate,
    db: Session = Depends(get_db),
    current_user: User = admin_dep,
):
    """Admin: update a device unit's condition, status, or serial number."""
    return device_service.update_unit(db, unit_id, body)


@router.delete("/units/{unit_id}", response_model=MessageResponse)
def delete_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Admin: delete a device unit (only if it has no trial history). Admin only."""
    device_service.delete_unit(db, unit_id)
    return {"message": "Device unit deleted successfully"}


@router.get("/units/device/{device_id}/status-counts")
def get_unit_status_counts(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = admin_dep,
):
    """Admin: get unit counts grouped by status for a specific device."""
    return device_service.get_unit_status_counts(db, device_id)
