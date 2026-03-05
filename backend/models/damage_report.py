"""
DamageReport model — customer-submitted reports of device damage during trials.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class DamageSeverity(str, enum.Enum):
    COSMETIC = "cosmetic"
    FUNCTIONAL = "functional"
    SEVERE = "severe"


class DamageStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"


class DamageReport(Base):
    __tablename__ = "damage_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    trial_id: Mapped[int] = mapped_column(ForeignKey("trials.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    device_unit_id: Mapped[int] = mapped_column(ForeignKey("device_units.id"), nullable=False, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    photos: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    severity: Mapped[DamageSeverity] = mapped_column(Enum(DamageSeverity), nullable=False)

    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deposit_deduction: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[DamageStatus] = mapped_column(Enum(DamageStatus), default=DamageStatus.SUBMITTED, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    trial: Mapped["Trial"] = relationship(back_populates="damage_reports")  # type: ignore[name-defined]
    user: Mapped["User"] = relationship(back_populates="damage_reports")  # type: ignore[name-defined]
    device_unit: Mapped["DeviceUnit"] = relationship(back_populates="damage_reports")  # type: ignore[name-defined]
