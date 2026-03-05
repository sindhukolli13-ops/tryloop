"""
AuditLog model — records admin actions and sensitive user actions for compliance.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. "trial.created", "payment.refunded"
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "trial", "device_unit"
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)  # extra context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # supports IPv6

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
