"""
Payments router — Stripe webhook endpoint and payment history.
The webhook receives events from Stripe to confirm payments and handle expirations.
"""

import logging

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, require_role
from models.user import User, UserRole
from repositories import payment_repo
from schemas.trial import PaymentResponse
from services import stripe_service, trial_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(alias="stripe-signature"),
):
    """
    Stripe webhook endpoint. Verifies the signature and dispatches events.
    Must be configured in the Stripe Dashboard to receive:
    - checkout.session.completed
    - checkout.session.expired
    """
    payload = await request.body()
    event = stripe_service.construct_webhook_event(payload, stripe_signature)

    event_type = event["type"]
    session_data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        trial_service.handle_checkout_completed(db, session_data)
    elif event_type == "checkout.session.expired":
        trial_service.handle_checkout_expired(db, session_data)
    else:
        logger.info("Unhandled Stripe event type: %s", event_type)

    # Always return 200 so Stripe doesn't retry
    return {"status": "ok"}


@router.get("/my", response_model=list[PaymentResponse])
def list_my_payments(
    trial_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's payment history, optionally filtered by trial."""
    if trial_id:
        # Verify trial belongs to user before showing payments
        trial_service.get_trial(db, trial_id, user_id=current_user.id)
        payments = payment_repo.get_for_trial(db, trial_id)
    else:
        # Get all payments for user (query directly since no repo method yet)
        from models.payment import Payment
        payments = (
            db.query(Payment)
            .filter(Payment.user_id == current_user.id)
            .order_by(Payment.created_at.desc())
            .all()
        )
    return [
        PaymentResponse(
            id=p.id,
            user_id=p.user_id,
            trial_id=p.trial_id,
            purchase_id=p.purchase_id,
            type=p.type.value,
            amount=float(p.amount),
            currency=p.currency,
            stripe_intent_id=p.stripe_intent_id,
            status=p.status.value,
            created_at=p.created_at,
        )
        for p in payments
    ]
