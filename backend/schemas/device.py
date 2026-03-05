"""
Pydantic schemas for devices (product catalog) and device units (physical inventory).
Covers request validation and response serialization for both public and admin endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Device schemas ──

class DeviceCreate(BaseModel):
    """Admin request to add a new device to the catalog."""
    name: str = Field(..., min_length=1, max_length=255)
    brand: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    specs: dict | None = None  # flexible key-value spec storage (e.g. {"RAM": "8GB"})
    images: list[str] | None = None  # list of image URLs
    trial_price_7d: float = Field(..., gt=0)
    trial_price_14d: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    deposit_amount: float = Field(..., gt=0)
    is_featured: bool = False
    is_active: bool = True


class DeviceUpdate(BaseModel):
    """Admin request to update an existing device. All fields optional."""
    name: str | None = Field(None, min_length=1, max_length=255)
    brand: str | None = Field(None, min_length=1, max_length=100)
    category: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    specs: dict | None = None
    images: list[str] | None = None
    trial_price_7d: float | None = Field(None, gt=0)
    trial_price_14d: float | None = Field(None, gt=0)
    purchase_price: float | None = Field(None, gt=0)
    deposit_amount: float | None = Field(None, gt=0)
    is_featured: bool | None = None
    is_active: bool | None = None


class DeviceResponse(BaseModel):
    """Public device listing — returned to customers browsing the catalog."""
    id: int
    name: str
    brand: str
    category: str
    description: str | None
    specs: dict | None
    images: list[str] | None
    trial_price_7d: float
    trial_price_14d: float
    purchase_price: float
    deposit_amount: float
    is_featured: bool
    is_active: bool
    available_units: int  # count of units with status "available"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    """Paginated list of devices with total count for pagination."""
    items: list[DeviceResponse]
    total: int
    page: int
    page_size: int


# ── Device Unit schemas ──

class DeviceUnitCreate(BaseModel):
    """Admin request to register a new physical unit."""
    device_id: int
    serial_number: str = Field(..., min_length=1, max_length=100)
    condition_grade: str = Field(default="new")  # new, like_new, refurb_a, refurb_b


class DeviceUnitUpdate(BaseModel):
    """Admin request to update a device unit. All fields optional."""
    serial_number: str | None = Field(None, min_length=1, max_length=100)
    condition_grade: str | None = None
    status: str | None = None


class DeviceUnitResponse(BaseModel):
    """Device unit details — includes parent device info."""
    id: int
    device_id: int
    serial_number: str
    condition_grade: str
    status: str
    rental_count: int
    total_lifecycle_revenue: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceUnitListResponse(BaseModel):
    """Paginated list of device units."""
    items: list[DeviceUnitResponse]
    total: int
    page: int
    page_size: int


# ── Comparison schema ──

class DeviceCompareResponse(BaseModel):
    """Side-by-side comparison of up to 3 devices."""
    devices: list[DeviceResponse]
