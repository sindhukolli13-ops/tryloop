"""
Pydantic schemas for trials (rental flow) and payments.
Covers request validation and response serialization.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Trial schemas ──

class TrialCreateRequest(BaseModel):
    """Customer request to start a trial. Triggers Stripe checkout."""
    device_id: int
    duration_days: int = Field(..., description="Trial duration: 7 or 14 days")


class TrialResponse(BaseModel):
    """Trial details returned to the customer."""
    id: int
    user_id: int
    device_id: int
    device_unit_id: int
    duration_days: int
    start_date: date | None
    end_date: date | None
    status: str
    trial_fee: float
    deposit_amount: float
    stripe_payment_intent_id: str | None
    created_at: datetime
    updated_at: datetime

    # Nested device info for convenience
    device_name: str | None = None
    device_brand: str | None = None
    device_image: str | None = None

    model_config = {"from_attributes": True}


class TrialListResponse(BaseModel):
    """Paginated list of trials."""
    items: list[TrialResponse]
    total: int
    page: int
    page_size: int


class TrialStatusUpdate(BaseModel):
    """Admin request to advance a trial's lifecycle status."""
    status: str = Field(..., description="New status: shipped, active, returned, etc.")


class TrialCancelRequest(BaseModel):
    """Customer request to cancel a trial (only before shipment)."""
    reason: str | None = None


class ReturnProcessRequest(BaseModel):
    """Admin request to process a device return."""
    condition_on_return: str = Field(
        default="good",
        description="Condition: good, needs_cleaning, needs_repair, damaged",
    )
    deposit_deduction: float = Field(
        default=0.0,
        ge=0,
        description="Amount to deduct from deposit (for damage)",
    )


# ── Stripe checkout schemas ──

class CheckoutSessionResponse(BaseModel):
    """Returned after creating a Stripe checkout session."""
    checkout_url: str
    session_id: str
    trial_id: int


# ── Payment schemas ──

class PaymentResponse(BaseModel):
    """Payment record returned in API responses."""
    id: int
    user_id: int
    trial_id: int | None
    purchase_id: int | None
    type: str
    amount: float
    currency: str
    stripe_intent_id: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
