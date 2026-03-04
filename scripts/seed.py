"""
Tryloop — Database seed script.
Populates the database with realistic sample data for development and demos.

Run from inside the backend container:
    docker compose exec backend python /app/../scripts/seed.py

Or add the backend directory to PYTHONPATH and run directly:
    cd backend && python ../scripts/seed.py
"""

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add backend/ to the Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from core.database import Base, SessionLocal, engine
from models.user import User, UserRole
from models.device import Device
from models.device_unit import ConditionGrade, DeviceUnit, UnitStatus
from models.trial import Trial, TrialStatus
from models.purchase import Purchase
from models.payment import Payment, PaymentStatus, PaymentType
from models.damage_report import DamageReport, DamageSeverity, DamageStatus
from models.refurbishment_log import RefurbishmentLog, RefurbStatus, ReturnCondition
from models.sustainability_metric import SustainabilityMetric


def seed():
    """Create all tables and insert sample data."""
    # Create tables (in dev; in production, use Alembic migrations)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Skip if data already exists
        if db.query(User).first():
            print("Database already seeded — skipping.")
            return

        # ── Users ──
        admin = User(
            email="admin@tryloop.nl",
            name="Tryloop Admin",
            hashed_password="$2b$12$placeholder_hash_replace_me",  # placeholder — will use passlib in auth step
            role=UserRole.ADMIN,
            email_verified=True,
        )
        staff = User(
            email="staff@tryloop.nl",
            name="Jan de Vries",
            hashed_password="$2b$12$placeholder_hash_replace_me",
            role=UserRole.STAFF,
            email_verified=True,
        )
        customer1 = User(
            email="emma@example.com",
            name="Emma van den Berg",
            hashed_password="$2b$12$placeholder_hash_replace_me",
            role=UserRole.CUSTOMER,
            email_verified=True,
        )
        customer2 = User(
            email="lucas@example.com",
            name="Lucas Jansen",
            hashed_password="$2b$12$placeholder_hash_replace_me",
            role=UserRole.CUSTOMER,
            email_verified=True,
        )
        db.add_all([admin, staff, customer1, customer2])
        db.flush()  # get IDs assigned

        # ── Devices (product catalog) ──
        devices = [
            Device(
                name="iPhone 15 Pro",
                brand="Apple",
                category="phones",
                description="Latest iPhone with titanium design and A17 Pro chip.",
                specs={"storage": "256GB", "color": "Natural Titanium", "display": "6.1 inch"},
                images=["iphone15pro_1.jpg", "iphone15pro_2.jpg"],
                trial_price_7d=49.00,
                trial_price_14d=79.00,
                purchase_price=1199.00,
                deposit_amount=200.00,
                is_featured=True,
            ),
            Device(
                name="MacBook Air M3",
                brand="Apple",
                category="laptops",
                description="Thin and light laptop with the M3 chip. Perfect for everyday use.",
                specs={"storage": "512GB", "ram": "16GB", "display": "13.6 inch"},
                images=["macbook_air_m3_1.jpg"],
                trial_price_7d=79.00,
                trial_price_14d=129.00,
                purchase_price=1399.00,
                deposit_amount=300.00,
                is_featured=True,
            ),
            Device(
                name="iPad Air",
                brand="Apple",
                category="tablets",
                description="Versatile tablet with M1 chip for work and play.",
                specs={"storage": "256GB", "display": "10.9 inch", "color": "Blue"},
                images=["ipad_air_1.jpg"],
                trial_price_7d=39.00,
                trial_price_14d=59.00,
                purchase_price=699.00,
                deposit_amount=150.00,
                is_featured=True,
            ),
            Device(
                name="Samsung Galaxy S24 Ultra",
                brand="Samsung",
                category="phones",
                description="Premium Android phone with S Pen and AI features.",
                specs={"storage": "256GB", "color": "Titanium Gray", "display": "6.8 inch"},
                images=["galaxy_s24_1.jpg"],
                trial_price_7d=45.00,
                trial_price_14d=75.00,
                purchase_price=1099.00,
                deposit_amount=200.00,
                is_featured=False,
            ),
            Device(
                name="Sony WH-1000XM5",
                brand="Sony",
                category="headphones",
                description="Industry-leading noise cancelling headphones.",
                specs={"type": "Over-ear", "battery": "30 hours", "anc": "Yes"},
                images=["sony_xm5_1.jpg"],
                trial_price_7d=19.00,
                trial_price_14d=29.00,
                purchase_price=349.00,
                deposit_amount=75.00,
                is_featured=False,
            ),
            Device(
                name="Apple Watch Series 9",
                brand="Apple",
                category="wearables",
                description="Advanced health and fitness tracking on your wrist.",
                specs={"size": "45mm", "connectivity": "GPS + Cellular"},
                images=["apple_watch_9_1.jpg"],
                trial_price_7d=25.00,
                trial_price_14d=39.00,
                purchase_price=449.00,
                deposit_amount=100.00,
                is_featured=True,
            ),
        ]
        db.add_all(devices)
        db.flush()

        # ── Device Units (physical inventory) ──
        units = [
            # iPhone 15 Pro — 3 units
            DeviceUnit(device_id=devices[0].id, serial_number="APL-IP15P-001", condition_grade=ConditionGrade.NEW, status=UnitStatus.AVAILABLE),
            DeviceUnit(device_id=devices[0].id, serial_number="APL-IP15P-002", condition_grade=ConditionGrade.LIKE_NEW, status=UnitStatus.ACTIVE, rental_count=2, total_lifecycle_revenue=98.00),
            DeviceUnit(device_id=devices[0].id, serial_number="APL-IP15P-003", condition_grade=ConditionGrade.REFURB_A, status=UnitStatus.AVAILABLE, rental_count=4, total_lifecycle_revenue=196.00),
            # MacBook Air — 2 units
            DeviceUnit(device_id=devices[1].id, serial_number="APL-MBA-M3-001", condition_grade=ConditionGrade.NEW, status=UnitStatus.AVAILABLE),
            DeviceUnit(device_id=devices[1].id, serial_number="APL-MBA-M3-002", condition_grade=ConditionGrade.LIKE_NEW, status=UnitStatus.REFURBISHING, rental_count=1, total_lifecycle_revenue=79.00),
            # iPad Air — 2 units
            DeviceUnit(device_id=devices[2].id, serial_number="APL-IPAD-AIR-001", condition_grade=ConditionGrade.NEW, status=UnitStatus.AVAILABLE),
            DeviceUnit(device_id=devices[2].id, serial_number="APL-IPAD-AIR-002", condition_grade=ConditionGrade.REFURB_B, status=UnitStatus.AVAILABLE, rental_count=3, total_lifecycle_revenue=117.00),
            # Galaxy S24 — 2 units
            DeviceUnit(device_id=devices[3].id, serial_number="SAM-S24U-001", condition_grade=ConditionGrade.NEW, status=UnitStatus.AVAILABLE),
            DeviceUnit(device_id=devices[3].id, serial_number="SAM-S24U-002", condition_grade=ConditionGrade.NEW, status=UnitStatus.RESERVED),
            # Sony headphones — 1 unit
            DeviceUnit(device_id=devices[4].id, serial_number="SNY-XM5-001", condition_grade=ConditionGrade.NEW, status=UnitStatus.AVAILABLE),
            # Apple Watch — 2 units
            DeviceUnit(device_id=devices[5].id, serial_number="APL-AW9-001", condition_grade=ConditionGrade.NEW, status=UnitStatus.AVAILABLE),
            DeviceUnit(device_id=devices[5].id, serial_number="APL-AW9-002", condition_grade=ConditionGrade.LIKE_NEW, status=UnitStatus.AVAILABLE, rental_count=1, total_lifecycle_revenue=25.00),
        ]
        db.add_all(units)
        db.flush()

        # ── Trials ──
        now = datetime.now(timezone.utc)

        # Active trial — Emma is trying iPhone 15 Pro unit #2
        trial1 = Trial(
            user_id=customer1.id,
            device_id=devices[0].id,
            device_unit_id=units[1].id,
            duration_days=7,
            start_date=date.today() - timedelta(days=3),
            end_date=date.today() + timedelta(days=4),
            status=TrialStatus.ACTIVE,
            trial_fee=49.00,
            deposit_amount=200.00,
            stripe_payment_intent_id="pi_sample_001",
        )

        # Completed trial — Lucas returned MacBook Air unit #2 (now refurbishing)
        trial2 = Trial(
            user_id=customer2.id,
            device_id=devices[1].id,
            device_unit_id=units[4].id,
            duration_days=14,
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() - timedelta(days=6),
            status=TrialStatus.REFURBISHING,
            trial_fee=129.00,
            deposit_amount=300.00,
            stripe_payment_intent_id="pi_sample_002",
        )

        # Reserved trial — Lucas reserved Galaxy S24 unit #2
        trial3 = Trial(
            user_id=customer2.id,
            device_id=devices[3].id,
            device_unit_id=units[8].id,
            duration_days=7,
            start_date=None,
            end_date=None,
            status=TrialStatus.RESERVED,
            trial_fee=45.00,
            deposit_amount=200.00,
            stripe_payment_intent_id="pi_sample_003",
        )

        db.add_all([trial1, trial2, trial3])
        db.flush()

        # ── Payments ──
        payments = [
            # Trial 1 — Emma's iPhone trial
            Payment(user_id=customer1.id, trial_id=trial1.id, type=PaymentType.TRIAL_FEE, amount=49.00, status=PaymentStatus.SUCCEEDED, stripe_intent_id="pi_sample_001"),
            Payment(user_id=customer1.id, trial_id=trial1.id, type=PaymentType.DEPOSIT, amount=200.00, status=PaymentStatus.SUCCEEDED, stripe_intent_id="pi_sample_001"),
            # Trial 2 — Lucas's MacBook trial + deposit refund
            Payment(user_id=customer2.id, trial_id=trial2.id, type=PaymentType.TRIAL_FEE, amount=129.00, status=PaymentStatus.SUCCEEDED, stripe_intent_id="pi_sample_002"),
            Payment(user_id=customer2.id, trial_id=trial2.id, type=PaymentType.DEPOSIT, amount=300.00, status=PaymentStatus.SUCCEEDED, stripe_intent_id="pi_sample_002"),
            Payment(user_id=customer2.id, trial_id=trial2.id, type=PaymentType.DEPOSIT_REFUND, amount=300.00, status=PaymentStatus.SUCCEEDED, stripe_intent_id="pi_refund_002"),
            # Trial 3 — Lucas's Galaxy reservation
            Payment(user_id=customer2.id, trial_id=trial3.id, type=PaymentType.TRIAL_FEE, amount=45.00, status=PaymentStatus.SUCCEEDED, stripe_intent_id="pi_sample_003"),
            Payment(user_id=customer2.id, trial_id=trial3.id, type=PaymentType.DEPOSIT, amount=200.00, status=PaymentStatus.SUCCEEDED, stripe_intent_id="pi_sample_003"),
        ]
        db.add_all(payments)

        # ── Refurbishment Log — for returned MacBook ──
        refurb = RefurbishmentLog(
            device_unit_id=units[4].id,
            trial_id=trial2.id,
            condition_on_return=ReturnCondition.NEEDS_CLEANING,
            tasks={"steps": ["Clean exterior", "Test keyboard", "Run diagnostics"]},
            status=RefurbStatus.IN_PROGRESS,
            technician_notes="Minor smudges on screen, all hardware checks passed.",
        )
        db.add(refurb)

        # ── Sustainability Metrics — sample period ──
        metrics = SustainabilityMetric(
            period="2026-03",
            total_trials=3,
            total_devices_active=12,
            co2_saved_kg=500.00,
            devices_given_second_life=8,
            prevented_purchases=2,
            avg_lifecycle_loops=2.5,
        )
        db.add(metrics)

        db.commit()
        print("Database seeded successfully!")
        print(f"  - {4} users (1 admin, 1 staff, 2 customers)")
        print(f"  - {len(devices)} devices")
        print(f"  - {len(units)} device units")
        print(f"  - {3} trials (1 active, 1 refurbishing, 1 reserved)")
        print(f"  - {len(payments)} payments")
        print(f"  - 1 refurbishment log")
        print(f"  - 1 sustainability metric record")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
