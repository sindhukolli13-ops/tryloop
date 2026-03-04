"""
Device model — the product catalog (e.g. "iPhone 15 Pro", "MacBook Air M3").
Each device can have many physical units (DeviceUnit).
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # flexible spec storage
    images: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Pricing — stored as Numeric for precise currency handling
    trial_price_7d: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    trial_price_14d: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # soft-delete flag

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    units: Mapped[list["DeviceUnit"]] = relationship(back_populates="device")  # type: ignore[name-defined]
    trials: Mapped[list["Trial"]] = relationship(back_populates="device")  # type: ignore[name-defined]
