"""
SustainabilityMetric model — computed/cached sustainability stats per period.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class SustainabilityMetric(Base):
    __tablename__ = "sustainability_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # e.g. "2026-03", "2026-Q1"

    total_trials: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_devices_active: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    co2_saved_kg: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    devices_given_second_life: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prevented_purchases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_lifecycle_loops: Mapped[float] = mapped_column(Numeric(6, 2), default=0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
