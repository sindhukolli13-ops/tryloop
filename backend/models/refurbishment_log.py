"""
RefurbishmentLog model — tracks the refurbishment process after a device is returned.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ReturnCondition(str, enum.Enum):
    """Condition of the device when it arrives back."""
    GOOD = "good"
    NEEDS_CLEANING = "needs_cleaning"
    NEEDS_REPAIR = "needs_repair"
    DAMAGED = "damaged"


class RefurbStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RefurbishmentLog(Base):
    __tablename__ = "refurbishment_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_unit_id: Mapped[int] = mapped_column(ForeignKey("device_units.id"), nullable=False, index=True)
    trial_id: Mapped[int] = mapped_column(ForeignKey("trials.id"), nullable=False, index=True)

    condition_on_return: Mapped[ReturnCondition] = mapped_column(Enum(ReturnCondition), nullable=False)
    tasks: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # list of refurb tasks
    status: Mapped[RefurbStatus] = mapped_column(Enum(RefurbStatus), default=RefurbStatus.PENDING, nullable=False)
    technician_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    device_unit: Mapped["DeviceUnit"] = relationship(back_populates="refurbishment_logs")  # type: ignore[name-defined]
    trial: Mapped["Trial"] = relationship(back_populates="refurbishment_logs")  # type: ignore[name-defined]
