"""
Trial model — a customer's device trial rental.
Tracks the full lifecycle from reservation to return/refurbishment.
"""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class TrialStatus(str, enum.Enum):
    """Trial lifecycle states — see CLAUDE.md for the full state diagram."""
    RESERVED = "reserved"
    SHIPPED = "shipped"
    ACTIVE = "active"
    RETURNED = "returned"
    REFURBISHING = "refurbishing"
    READY = "ready"
    AVAILABLE = "available"
    CANCELLED = "cancelled"


class Trial(Base):
    __tablename__ = "trials"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # device_id is denormalized from device_units for faster "all trials for this model" queries
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    device_unit_id: Mapped[int] = mapped_column(ForeignKey("device_units.id"), nullable=False, index=True)

    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 7 or 14
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # set when shipped
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[TrialStatus] = mapped_column(Enum(TrialStatus), default=TrialStatus.RESERVED, nullable=False, index=True)

    trial_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="trials")  # type: ignore[name-defined]
    device: Mapped["Device"] = relationship(back_populates="trials")  # type: ignore[name-defined]
    device_unit: Mapped["DeviceUnit"] = relationship(back_populates="trials")  # type: ignore[name-defined]
    payments: Mapped[list["Payment"]] = relationship(back_populates="trial")  # type: ignore[name-defined]
    damage_reports: Mapped[list["DamageReport"]] = relationship(back_populates="trial")  # type: ignore[name-defined]
    refurbishment_logs: Mapped[list["RefurbishmentLog"]] = relationship(back_populates="trial")  # type: ignore[name-defined]
