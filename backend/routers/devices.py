"""
Devices router — public catalog browsing (list, detail, compare, filters)
and admin CRUD (create, update, delete devices).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_role
from models.user import User, UserRole
from schemas.auth import MessageResponse
from schemas.device import (
    DeviceCompareResponse,
    DeviceCreate,
    DeviceListResponse,
    DeviceResponse,
    DeviceUpdate,
)
from services import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


# ── Public endpoints (no auth required) ──

@router.get("", response_model=DeviceListResponse)
def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    brand: str | None = None,
    search: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    is_featured: bool | None = None,
    available_only: bool = False,
    db: Session = Depends(get_db),
):
    """Browse the device catalog with optional filtering and pagination."""
    return device_service.list_devices(
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


@router.get("/featured", response_model=list[DeviceResponse])
def get_featured_devices(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get featured devices for the homepage."""
    return device_service.get_featured_devices(db, limit=limit)


@router.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    """Get available categories and brands for filter dropdowns."""
    return device_service.get_filter_options(db)


@router.get("/compare", response_model=DeviceCompareResponse)
def compare_devices(
    ids: list[int] = Query(..., min_length=2, max_length=3),
    db: Session = Depends(get_db),
):
    """Compare 2-3 devices side by side. Pass device IDs as query params: ?ids=1&ids=2&ids=3"""
    return device_service.compare_devices(db, ids)


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get details for a single device."""
    return device_service.get_device(db, device_id)


# ── Admin endpoints (requires admin or staff role) ──

@router.post("", response_model=DeviceResponse, status_code=201)
def create_device(
    body: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
):
    """Admin: add a new device to the catalog."""
    return device_service.create_device(db, body)


@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    body: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
):
    """Admin: update an existing device."""
    return device_service.update_device(db, device_id, body)


@router.delete("/{device_id}", response_model=MessageResponse)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Admin: soft-delete a device (marks as inactive). Admin only."""
    device_service.delete_device(db, device_id)
    return {"message": "Device deleted successfully"}
