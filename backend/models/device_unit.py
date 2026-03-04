"""
DeviceUnit model — a single physical unit tracked by serial number.
Each unit belongs to a Device (product) and goes through its own lifecycle.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ConditionGrade(str, enum.Enum):
    """Physical condition of a device unit."""
    NEW = "new"
    LIKE_NEW = "like_new"
    REFURB_A = "refurb_a"
    REFURB_B = "refurb_b"


class UnitStatus(str, enum.Enum):
    """Current lifecycle status of a device unit."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SHIPPED = "shipped"
    ACTIVE = "active"        # currently on trial
    RETURNED = "returned"
    REFURBISHING = "refurbishing"
    RETIRED = "retired"      # no longer in circulation
    SOLD = "sold"            # purchased through the shop


class DeviceUnit(Base):
    __tablename__ = "device_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    condition_grade: Mapped[ConditionGrade] = mapped_column(Enum(ConditionGrade), default=ConditionGrade.NEW, nullable=False)
    status: Mapped[UnitStatus] = mapped_column(Enum(UnitStatus), default=UnitStatus.AVAILABLE, nullable=False, index=True)
    rental_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_lifecycle_revenue: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device: Mapped["Device"] = relationship(back_populates="units")  # type: ignore[name-defined]
    trials: Mapped[list["Trial"]] = relationship(back_populates="device_unit")  # type: ignore[name-defined]
    refurbishment_logs: Mapped[list["RefurbishmentLog"]] = relationship(back_populates="device_unit")  # type: ignore[name-defined]
    damage_reports: Mapped[list["DamageReport"]] = relationship(back_populates="device_unit")  # type: ignore[name-defined]
