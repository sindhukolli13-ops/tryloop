"""Initial schema — all 10 tables for Tryloop.

Revision ID: 0001
Revises: None
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("customer", "admin", "staff", name="userrole"), nullable=False, server_default="customer"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── devices (product catalog) ──
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("brand", sa.String(100), nullable=False, index=True),
        sa.Column("category", sa.String(100), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specs", postgresql.JSON(), nullable=True),
        sa.Column("images", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("trial_price_7d", sa.Numeric(10, 2), nullable=False),
        sa.Column("trial_price_14d", sa.Numeric(10, 2), nullable=False),
        sa.Column("purchase_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── device_units (physical inventory) ──
    op.create_table(
        "device_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False, index=True),
        sa.Column("serial_number", sa.String(100), unique=True, nullable=False),
        sa.Column("condition_grade", sa.Enum("new", "like_new", "refurb_a", "refurb_b", name="conditiongrade"), nullable=False, server_default="new"),
        sa.Column("status", sa.Enum("available", "reserved", "shipped", "active", "returned", "refurbishing", "retired", "sold", name="unitstatus"), nullable=False, server_default="available", index=True),
        sa.Column("rental_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_lifecycle_revenue", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── trials ──
    op.create_table(
        "trials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False, index=True),
        sa.Column("device_unit_id", sa.Integer(), sa.ForeignKey("device_units.id"), nullable=False, index=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("reserved", "shipped", "active", "returned", "refurbishing", "ready", "available", "cancelled", name="trialstatus"), nullable=False, server_default="reserved", index=True),
        sa.Column("trial_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── purchases ──
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False, index=True),
        sa.Column("device_unit_id", sa.Integer(), sa.ForeignKey("device_units.id"), nullable=False, index=True),
        sa.Column("purchase_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── payments ──
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("trial_id", sa.Integer(), sa.ForeignKey("trials.id"), nullable=True, index=True),
        sa.Column("purchase_id", sa.Integer(), sa.ForeignKey("purchases.id"), nullable=True, index=True),
        sa.Column("type", sa.Enum("trial_fee", "deposit", "deposit_refund", "purchase", "refund", name="paymenttype"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("stripe_intent_id", sa.String(255), nullable=True),
        sa.Column("status", sa.Enum("pending", "succeeded", "failed", "refunded", name="paymentstatus"), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── damage_reports ──
    op.create_table(
        "damage_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trial_id", sa.Integer(), sa.ForeignKey("trials.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("device_unit_id", sa.Integer(), sa.ForeignKey("device_units.id"), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("photos", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("severity", sa.Enum("cosmetic", "functional", "severe", name="damageseverity"), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("deposit_deduction", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.Enum("submitted", "under_review", "resolved", name="damagestatus"), nullable=False, server_default="submitted"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── refurbishment_logs ──
    op.create_table(
        "refurbishment_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_unit_id", sa.Integer(), sa.ForeignKey("device_units.id"), nullable=False, index=True),
        sa.Column("trial_id", sa.Integer(), sa.ForeignKey("trials.id"), nullable=False, index=True),
        sa.Column("condition_on_return", sa.Enum("good", "needs_cleaning", "needs_repair", "damaged", name="returncondition"), nullable=False),
        sa.Column("tasks", postgresql.JSON(), nullable=True),
        sa.Column("status", sa.Enum("pending", "in_progress", "completed", name="refurbstatus"), nullable=False, server_default="pending"),
        sa.Column("technician_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── audit_logs ──
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── sustainability_metrics ──
    op.create_table(
        "sustainability_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("period", sa.String(20), nullable=False, index=True),
        sa.Column("total_trials", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_devices_active", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("co2_saved_kg", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("devices_given_second_life", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("prevented_purchases", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_lifecycle_loops", sa.Numeric(6, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sustainability_metrics")
    op.drop_table("audit_logs")
    op.drop_table("refurbishment_logs")
    op.drop_table("damage_reports")
    op.drop_table("payments")
    op.drop_table("purchases")
    op.drop_table("trials")
    op.drop_table("device_units")
    op.drop_table("devices")
    op.drop_table("users")

    # Drop all enum types
    for enum_name in [
        "userrole", "conditiongrade", "unitstatus", "trialstatus",
        "paymenttype", "paymentstatus", "damageseverity", "damagestatus",
        "returncondition", "refurbstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
