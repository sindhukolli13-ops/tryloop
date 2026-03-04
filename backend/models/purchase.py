"""
Purchase model — direct purchase of new/unused products (separate from trials).
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    device_unit_id: Mapped[int] = mapped_column(ForeignKey("device_units.id"), nullable=False, index=True)

    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="purchases")  # type: ignore[name-defined]
    payments: Mapped[list["Payment"]] = relationship(back_populates="purchase")  # type: ignore[name-defined]
