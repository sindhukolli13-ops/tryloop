"""
Payment model — all money movements (trial fees, deposits, refunds, purchases).
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class PaymentType(str, enum.Enum):
    """What this payment is for."""
    TRIAL_FEE = "trial_fee"
    DEPOSIT = "deposit"
    DEPOSIT_REFUND = "deposit_refund"
    PURCHASE = "purchase"
    REFUND = "refund"


class PaymentStatus(str, enum.Enum):
    """Stripe payment lifecycle."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    trial_id: Mapped[int | None] = mapped_column(ForeignKey("trials.id"), nullable=True, index=True)
    purchase_id: Mapped[int | None] = mapped_column(ForeignKey("purchases.id"), nullable=True, index=True)

    type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    stripe_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trial: Mapped["Trial | None"] = relationship(back_populates="payments")  # type: ignore[name-defined]
    purchase: Mapped["Purchase | None"] = relationship(back_populates="payments")  # type: ignore[name-defined]
