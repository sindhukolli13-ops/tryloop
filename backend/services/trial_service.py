"""
Trial service — business logic for the trial rental flow.
Handles trial creation, Stripe checkout, state machine transitions,
cancellation, and return processing.
"""

import logging
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from models.device_unit import UnitStatus
from models.payment import PaymentStatus, PaymentType
from models.trial import Trial, TrialStatus
from models.refurbishment_log import ReturnCondition
from repositories import device_repo, device_unit_repo, payment_repo, refurbishment_repo, trial_repo
from schemas.trial import (
    CheckoutSessionResponse,
    TrialListResponse,
    TrialResponse,
)
from services import stripe_service

logger = logging.getLogger(__name__)

# ── Valid state transitions (state machine) ──
# Maps current status → set of allowed next statuses
VALID_TRANSITIONS: dict[TrialStatus, set[TrialStatus]] = {
    TrialStatus.RESERVED: {TrialStatus.SHIPPED, TrialStatus.CANCELLED},
    TrialStatus.SHIPPED: {TrialStatus.ACTIVE},
    TrialStatus.ACTIVE: {TrialStatus.RETURNED},
    TrialStatus.RETURNED: {TrialStatus.REFURBISHING},
    TrialStatus.REFURBISHING: {TrialStatus.READY},
    TrialStatus.READY: {TrialStatus.AVAILABLE},
    # Terminal states — no further transitions
    TrialStatus.AVAILABLE: set(),
    TrialStatus.CANCELLED: set(),
}

# Map trial status → corresponding device unit status
TRIAL_TO_UNIT_STATUS: dict[TrialStatus, UnitStatus] = {
    TrialStatus.RESERVED: UnitStatus.RESERVED,
    TrialStatus.SHIPPED: UnitStatus.SHIPPED,
    TrialStatus.ACTIVE: UnitStatus.ACTIVE,
    TrialStatus.RETURNED: UnitStatus.RETURNED,
    TrialStatus.REFURBISHING: UnitStatus.REFURBISHING,
    TrialStatus.READY: UnitStatus.AVAILABLE,
    TrialStatus.AVAILABLE: UnitStatus.AVAILABLE,
    TrialStatus.CANCELLED: UnitStatus.AVAILABLE,
}


# ── Helpers ──

def _trial_to_response(trial: Trial) -> TrialResponse:
    """Convert a Trial ORM object to a TrialResponse."""
    device = trial.device
    return TrialResponse(
        id=trial.id,
        user_id=trial.user_id,
        device_id=trial.device_id,
        device_unit_id=trial.device_unit_id,
        duration_days=trial.duration_days,
        start_date=trial.start_date,
        end_date=trial.end_date,
        status=trial.status.value,
        trial_fee=float(trial.trial_fee),
        deposit_amount=float(trial.deposit_amount),
        stripe_payment_intent_id=trial.stripe_payment_intent_id,
        created_at=trial.created_at,
        updated_at=trial.updated_at,
        device_name=device.name if device else None,
        device_brand=device.brand if device else None,
        device_image=(device.images[0] if device and device.images else None),
    )


def _validate_transition(current: TrialStatus, target: TrialStatus) -> None:
    """Raise 400 if the requested state transition is not allowed."""
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{current.value}' to '{target.value}'",
        )


# ── Trial creation + checkout ──

def create_trial_checkout(
    db: Session,
    *,
    user_id: int,
    user_email: str,
    device_id: int,
    duration_days: int,
) -> CheckoutSessionResponse:
    """
    Create a trial and a Stripe checkout session.
    1. Validate device and duration
    2. Find an available unit
    3. Reserve the unit (prevent double-booking)
    4. Create the trial record
    5. Create Stripe checkout session
    """
    # Validate duration
    if duration_days not in settings.TRIAL_DURATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid duration. Allowed: {settings.TRIAL_DURATIONS}",
        )

    # Validate device exists
    device = device_repo.get_by_id(db, device_id)
    if not device or not device.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    # Find an available unit
    available_units = device_unit_repo.get_available_for_device(db, device_id)
    if not available_units:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No units available for this device",
        )

    # Pick the first available unit and reserve it immediately
    unit = available_units[0]
    device_unit_repo.update(db, unit, data={"status": UnitStatus.RESERVED})

    # Determine pricing based on duration
    trial_fee = float(device.trial_price_7d if duration_days == 7 else device.trial_price_14d)
    deposit_amount = float(device.deposit_amount)

    # Create trial record in RESERVED status
    trial = trial_repo.create(db, data={
        "user_id": user_id,
        "device_id": device_id,
        "device_unit_id": unit.id,
        "duration_days": duration_days,
        "status": TrialStatus.RESERVED,
        "trial_fee": trial_fee,
        "deposit_amount": deposit_amount,
    })

    # Create Stripe checkout session
    frontend_url = settings.NEXTAUTH_URL
    session = stripe_service.create_checkout_session(
        trial_id=trial.id,
        device_name=device.name,
        trial_fee=trial_fee,
        deposit_amount=deposit_amount,
        duration_days=duration_days,
        customer_email=user_email,
        success_url=f"{frontend_url}/checkout/success?trial_id={trial.id}",
        cancel_url=f"{frontend_url}/checkout/cancel?trial_id={trial.id}",
    )

    # Store the Stripe session ID on the trial for webhook matching
    trial_repo.update(db, trial, data={
        "stripe_payment_intent_id": session.payment_intent or session.id,
    })

    logger.info(
        "Trial created: id=%d device=%d unit=%d user=%d",
        trial.id, device_id, unit.id, user_id,
    )

    return CheckoutSessionResponse(
        checkout_url=session.url,
        session_id=session.id,
        trial_id=trial.id,
    )


# ── Stripe webhook handler ──

def handle_checkout_completed(db: Session, session_data: dict) -> None:
    """
    Called by the Stripe webhook when checkout.session.completed fires.
    Confirms payment and creates payment records for the trial.
    """
    trial_id = int(session_data.get("metadata", {}).get("trial_id", 0))
    if not trial_id:
        logger.warning("Webhook missing trial_id in metadata")
        return

    trial = trial_repo.get_by_id(db, trial_id)
    if not trial:
        logger.warning("Webhook: trial %d not found", trial_id)
        return

    if trial.status != TrialStatus.RESERVED:
        logger.info("Webhook: trial %d already past RESERVED, skipping", trial_id)
        return

    payment_intent_id = session_data.get("payment_intent")

    # Update trial with Stripe payment intent
    if payment_intent_id:
        trial_repo.update(db, trial, data={"stripe_payment_intent_id": payment_intent_id})

    # Create payment records — one for trial fee, one for deposit
    payment_repo.create(db, data={
        "user_id": trial.user_id,
        "trial_id": trial.id,
        "type": PaymentType.TRIAL_FEE,
        "amount": float(trial.trial_fee),
        "currency": "EUR",
        "stripe_intent_id": payment_intent_id,
        "status": PaymentStatus.SUCCEEDED,
    })
    payment_repo.create(db, data={
        "user_id": trial.user_id,
        "trial_id": trial.id,
        "type": PaymentType.DEPOSIT,
        "amount": float(trial.deposit_amount),
        "currency": "EUR",
        "stripe_intent_id": payment_intent_id,
        "status": PaymentStatus.SUCCEEDED,
    })

    logger.info("Payment confirmed for trial %d (PI: %s)", trial_id, payment_intent_id)


def handle_checkout_expired(db: Session, session_data: dict) -> None:
    """
    Called when a Stripe checkout session expires without payment.
    Releases the reserved unit and cancels the trial.
    """
    trial_id = int(session_data.get("metadata", {}).get("trial_id", 0))
    if not trial_id:
        return

    trial = trial_repo.get_by_id(db, trial_id)
    if not trial or trial.status != TrialStatus.RESERVED:
        return

    # Release the reserved unit
    unit = device_unit_repo.get_by_id(db, trial.device_unit_id)
    if unit:
        device_unit_repo.update(db, unit, data={"status": UnitStatus.AVAILABLE})

    trial_repo.update_status(db, trial, TrialStatus.CANCELLED)
    logger.info("Trial %d cancelled — checkout session expired", trial_id)


# ── Trial lifecycle management ──

def get_trial(db: Session, trial_id: int, *, user_id: int | None = None) -> TrialResponse:
    """Get a single trial. If user_id is provided, ensures the trial belongs to that user."""
    trial = trial_repo.get_by_id(db, trial_id)
    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial not found")
    if user_id and trial.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your trial")
    return _trial_to_response(trial)


def list_user_trials(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> TrialListResponse:
    """List trials for a specific customer."""
    trials, total = trial_repo.get_user_trials(
        db, user_id, page=page, page_size=page_size, status=status,
    )
    items = [_trial_to_response(t) for t in trials]
    return TrialListResponse(items=items, total=total, page=page, page_size=page_size)


def list_all_trials(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    user_id: int | None = None,
    device_id: int | None = None,
    overdue_only: bool = False,
) -> TrialListResponse:
    """Admin: list all trials with filtering."""
    trials, total = trial_repo.get_all(
        db,
        page=page,
        page_size=page_size,
        status=status,
        user_id=user_id,
        device_id=device_id,
        overdue_only=overdue_only,
    )
    items = [_trial_to_response(t) for t in trials]
    return TrialListResponse(items=items, total=total, page=page, page_size=page_size)


def update_trial_status(
    db: Session,
    trial_id: int,
    new_status_str: str,
) -> TrialResponse:
    """
    Admin: advance a trial to a new lifecycle status.
    Validates the transition and updates the device unit status accordingly.
    """
    trial = trial_repo.get_by_id(db, trial_id)
    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial not found")

    new_status = TrialStatus(new_status_str)
    _validate_transition(trial.status, new_status)

    # Set start/end dates when trial becomes active (shipped → active)
    update_data: dict = {}
    if new_status == TrialStatus.ACTIVE and not trial.start_date:
        update_data["start_date"] = date.today()
        update_data["end_date"] = date.today() + timedelta(days=trial.duration_days)

    # Update the device unit status to mirror the trial status
    unit = device_unit_repo.get_by_id(db, trial.device_unit_id)
    if unit:
        target_unit_status = TRIAL_TO_UNIT_STATUS.get(new_status)
        if target_unit_status:
            device_unit_repo.update(db, unit, data={"status": target_unit_status})

        # When trial completes full cycle (READY→AVAILABLE), increment rental count
        if new_status == TrialStatus.AVAILABLE:
            device_unit_repo.update(db, unit, data={
                "rental_count": unit.rental_count + 1,
                "total_lifecycle_revenue": float(unit.total_lifecycle_revenue) + float(trial.trial_fee),
            })

    # Apply status + any date updates
    update_data["status"] = new_status
    trial_repo.update(db, trial, data=update_data)

    logger.info("Trial %d status updated: %s → %s", trial_id, trial.status.value, new_status.value)
    return _trial_to_response(trial)


def cancel_trial(
    db: Session,
    trial_id: int,
    *,
    user_id: int | None = None,
) -> TrialResponse:
    """
    Cancel a trial. Only allowed when status is RESERVED (before shipment).
    Releases the reserved unit and triggers a full refund via Stripe.
    """
    trial = trial_repo.get_by_id(db, trial_id)
    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial not found")
    if user_id and trial.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your trial")

    _validate_transition(trial.status, TrialStatus.CANCELLED)

    # Release the reserved unit
    unit = device_unit_repo.get_by_id(db, trial.device_unit_id)
    if unit:
        device_unit_repo.update(db, unit, data={"status": UnitStatus.AVAILABLE})

    # Issue full refund via Stripe if payment was made
    if trial.stripe_payment_intent_id:
        stripe_service.create_refund(payment_intent_id=trial.stripe_payment_intent_id)

        # Record refund payment
        total_paid = float(trial.trial_fee) + float(trial.deposit_amount)
        payment_repo.create(db, data={
            "user_id": trial.user_id,
            "trial_id": trial.id,
            "type": PaymentType.REFUND,
            "amount": total_paid,
            "currency": "EUR",
            "stripe_intent_id": trial.stripe_payment_intent_id,
            "status": PaymentStatus.REFUNDED,
        })

    trial_repo.update_status(db, trial, TrialStatus.CANCELLED)
    logger.info("Trial %d cancelled by user %d", trial_id, trial.user_id)
    return _trial_to_response(trial)


# ── Return processing + deposit refund ──

def process_return(
    db: Session,
    trial_id: int,
    *,
    condition_on_return: str = "good",
    deposit_deduction: float = 0.0,
) -> TrialResponse:
    """
    Admin: process a device return.
    1. Validate trial is in ACTIVE status
    2. Transition trial to RETURNED
    3. Update device unit status to RETURNED
    4. Process deposit refund via Stripe (minus any deduction)
    5. Create a refurbishment log entry
    """
    trial = trial_repo.get_by_id(db, trial_id)
    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial not found")

    _validate_transition(trial.status, TrialStatus.RETURNED)

    # Validate deduction doesn't exceed deposit
    deposit = float(trial.deposit_amount)
    if deposit_deduction < 0 or deposit_deduction > deposit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deduction must be between 0 and {deposit}",
        )

    # Transition trial → RETURNED
    trial_repo.update_status(db, trial, TrialStatus.RETURNED)

    # Update device unit → RETURNED
    unit = device_unit_repo.get_by_id(db, trial.device_unit_id)
    if unit:
        device_unit_repo.update(db, unit, data={"status": UnitStatus.RETURNED})

    # Process deposit refund via Stripe (deposit minus any damage deduction)
    refund_amount = deposit - deposit_deduction
    if refund_amount > 0 and trial.stripe_payment_intent_id:
        refund_cents = int(refund_amount * 100)
        stripe_service.create_refund(
            payment_intent_id=trial.stripe_payment_intent_id,
            amount_cents=refund_cents,
        )

        # Record deposit refund payment
        payment_repo.create(db, data={
            "user_id": trial.user_id,
            "trial_id": trial.id,
            "type": PaymentType.DEPOSIT_REFUND,
            "amount": refund_amount,
            "currency": "EUR",
            "stripe_intent_id": trial.stripe_payment_intent_id,
            "status": PaymentStatus.REFUNDED,
        })

    # Auto-create refurbishment log entry so admin can track the refurb process
    refurbishment_repo.create(db, data={
        "device_unit_id": trial.device_unit_id,
        "trial_id": trial.id,
        "condition_on_return": condition_on_return,
        "status": "pending",
        "tasks": [],
    })

    logger.info(
        "Trial %d returned: deposit refund=%.2f deduction=%.2f condition=%s",
        trial_id, refund_amount, deposit_deduction, condition_on_return,
    )
    return _trial_to_response(trial)


def request_return(
    db: Session,
    trial_id: int,
    *,
    user_id: int,
) -> TrialResponse:
    """
    Customer: request a return for an active trial.
    This is a soft action — marks the trial as ready for return processing.
    The actual return is finalized by admin via process_return().
    For now, this just validates the trial is active and belongs to the user.
    """
    trial = trial_repo.get_by_id(db, trial_id)
    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial not found")
    if trial.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your trial")

    if trial.status != TrialStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active trials can be returned",
        )

    # For the MVP, the customer "requesting" a return is informational.
    # The actual state change happens when admin processes the return.
    # We return the trial as-is with instructions.
    logger.info("Return requested for trial %d by user %d", trial_id, user_id)
    return _trial_to_response(trial)
