"""
Trials router — customer trial creation, checkout, cancellation,
and admin trial lifecycle management.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, require_role
from models.user import User, UserRole
from schemas.auth import MessageResponse
from schemas.trial import (
    CheckoutSessionResponse,
    ReturnProcessRequest,
    TrialCancelRequest,
    TrialCreateRequest,
    TrialListResponse,
    TrialResponse,
    TrialStatusUpdate,
)
from services import trial_service

router = APIRouter(prefix="/trials", tags=["trials"])


# ── Customer endpoints ──

@router.post("/checkout", response_model=CheckoutSessionResponse, status_code=201)
def create_trial_checkout(
    body: TrialCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a trial: reserve a unit and create a Stripe checkout session."""
    return trial_service.create_trial_checkout(
        db,
        user_id=current_user.id,
        user_email=current_user.email,
        device_id=body.device_id,
        duration_days=body.duration_days,
    )


@router.get("/my", response_model=TrialListResponse)
def list_my_trials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's trials."""
    return trial_service.list_user_trials(
        db, current_user.id, page=page, page_size=page_size, status=status,
    )


@router.get("/my/{trial_id}", response_model=TrialResponse)
def get_my_trial(
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of one of the current user's trials."""
    return trial_service.get_trial(db, trial_id, user_id=current_user.id)


@router.post("/my/{trial_id}/cancel", response_model=TrialResponse)
def cancel_my_trial(
    trial_id: int,
    body: TrialCancelRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a trial (only before shipment). Triggers full refund."""
    return trial_service.cancel_trial(db, trial_id, user_id=current_user.id)


@router.post("/my/{trial_id}/return", response_model=TrialResponse)
def request_return(
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Customer: request a return for an active trial."""
    return trial_service.request_return(db, trial_id, user_id=current_user.id)


# ── Admin endpoints ──

@router.get("", response_model=TrialListResponse)
def list_all_trials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    user_id: int | None = None,
    device_id: int | None = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
):
    """Admin: list all trials with filtering."""
    return trial_service.list_all_trials(
        db,
        page=page,
        page_size=page_size,
        status=status,
        user_id=user_id,
        device_id=device_id,
        overdue_only=overdue_only,
    )


@router.get("/{trial_id}", response_model=TrialResponse)
def get_trial(
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
):
    """Admin: get details for any trial."""
    return trial_service.get_trial(db, trial_id)


@router.patch("/{trial_id}/status", response_model=TrialResponse)
def update_trial_status(
    trial_id: int,
    body: TrialStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
):
    """Admin: advance a trial to the next lifecycle status."""
    return trial_service.update_trial_status(db, trial_id, body.status)


@router.post("/{trial_id}/cancel", response_model=TrialResponse)
def admin_cancel_trial(
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Admin: cancel any trial (only before shipment). Admin only."""
    return trial_service.cancel_trial(db, trial_id)


@router.post("/{trial_id}/return", response_model=TrialResponse)
def process_return(
    trial_id: int,
    body: ReturnProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
):
    """Admin: process a device return with deposit refund and refurbishment log."""
    return trial_service.process_return(
        db,
        trial_id,
        condition_on_return=body.condition_on_return,
        deposit_deduction=body.deposit_deduction,
    )
