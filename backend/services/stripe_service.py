"""
Stripe service — handles checkout session creation, webhook verification,
and refund processing. Wraps the Stripe SDK.
"""

import logging

import stripe
from fastapi import HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)

# Configure Stripe SDK with our secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(
    *,
    trial_id: int,
    device_name: str,
    trial_fee: float,
    deposit_amount: float,
    duration_days: int,
    customer_email: str,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout Session for a trial booking.
    Two line items: the non-refundable trial fee + the refundable deposit.
    """
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=customer_email,
            # Store trial_id in metadata so the webhook can link back
            metadata={"trial_id": str(trial_id)},
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": int(trial_fee * 100),  # Stripe uses cents
                        "product_data": {
                            "name": f"{device_name} — {duration_days}-day trial fee",
                            "description": "Non-refundable trial fee",
                        },
                    },
                    "quantity": 1,
                },
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": int(deposit_amount * 100),
                        "product_data": {
                            "name": f"{device_name} — Refundable deposit",
                            "description": "Fully refunded on return in acceptable condition",
                        },
                    },
                    "quantity": 1,
                },
            ],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        logger.info("Stripe checkout session created: %s for trial %d", session.id, trial_id)
        return session
    except stripe.StripeError as e:
        logger.error("Stripe checkout error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error. Please try again.",
        )


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and parse a Stripe webhook event using the signing secret."""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )
    except ValueError:
        logger.warning("Stripe webhook payload invalid")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )


def create_refund(
    *,
    payment_intent_id: str,
    amount_cents: int | None = None,
    reason: str = "requested_by_customer",
) -> stripe.Refund:
    """
    Issue a refund via Stripe. If amount_cents is None, refunds the full amount.
    Used for deposit refunds and trial cancellation refunds.
    """
    try:
        params: dict = {
            "payment_intent": payment_intent_id,
            "reason": reason,
        }
        if amount_cents is not None:
            params["amount"] = amount_cents

        refund = stripe.Refund.create(**params)
        logger.info("Stripe refund created: %s for PI %s", refund.id, payment_intent_id)
        return refund
    except stripe.StripeError as e:
        logger.error("Stripe refund error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Refund processing failed. Please try again.",
        )
