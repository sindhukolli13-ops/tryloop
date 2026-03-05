"""
Payment repository — database queries for payment records.
"""

from sqlalchemy.orm import Session

from models.payment import Payment, PaymentStatus, PaymentType


def get_by_id(db: Session, payment_id: int) -> Payment | None:
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_by_stripe_intent(db: Session, stripe_intent_id: str) -> Payment | None:
    return (
        db.query(Payment)
        .filter(Payment.stripe_intent_id == stripe_intent_id)
        .first()
    )


def get_for_trial(db: Session, trial_id: int) -> list[Payment]:
    """Get all payments associated with a trial."""
    return (
        db.query(Payment)
        .filter(Payment.trial_id == trial_id)
        .order_by(Payment.created_at.asc())
        .all()
    )


def create(db: Session, *, data: dict) -> Payment:
    """Create a new payment record."""
    # Convert string enum values
    if "type" in data and isinstance(data["type"], str):
        data["type"] = PaymentType(data["type"])
    if "status" in data and isinstance(data["status"], str):
        data["status"] = PaymentStatus(data["status"])

    payment = Payment(**data)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def update_status(db: Session, payment: Payment, new_status: PaymentStatus) -> Payment:
    """Update only the status of a payment."""
    payment.status = new_status
    db.commit()
    db.refresh(payment)
    return payment
