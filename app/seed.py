from datetime import datetime, timedelta

from app.models import (
    Booking,
    BookingStatusEnum,
    Payment,
    PaymentStatusEnum,
    Review,
    RoleEnum,
    Service,
    ServiceStatusEnum,
    SlotStatusEnum,
    TimeSlot,
    User,
    UserProfile,
)
from app.security import hash_password


def seed_demo_data(session):
    if session.query(User).filter(User.username == "admin").first():
        return

    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role=RoleEnum.ADMIN,
        is_active=True,
        profile=UserProfile(full_name="Demo Admin", phone="+98-000", bio="System administrator"),
    )
    provider = User(
        username="provider",
        email="provider@example.com",
        password_hash=hash_password("provider123"),
        role=RoleEnum.PROVIDER,
        is_active=True,
        profile=UserProfile(full_name="Demo Provider", phone="+98-111", bio="Provides home and repair services"),
    )
    customer = User(
        username="customer",
        email="customer@example.com",
        password_hash=hash_password("customer123"),
        role=RoleEnum.CUSTOMER,
        is_active=True,
        profile=UserProfile(full_name="Demo Customer", phone="+98-222", bio="Demo customer account"),
    )
    session.add_all([admin, provider, customer])
    session.flush()

    cleaning = Service(
        provider_id=provider.id,
        title="Home Cleaning",
        description="Standard apartment cleaning for a demo booking workflow.",
        category="Cleaning",
        duration_minutes=60,
        price=2_500_000,
        status=ServiceStatusEnum.ACTIVE,
    )
    repair = Service(
        provider_id=provider.id,
        title="Appliance Repair",
        description="Mock appliance repair service with a longer slot duration.",
        category="Repair",
        duration_minutes=90,
        price=4_000_000,
        status=ServiceStatusEnum.ACTIVE,
    )
    session.add_all([cleaning, repair])
    session.flush()

    base = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(days=2)
    slot1 = TimeSlot(service_id=cleaning.id, start_time=base, end_time=base + timedelta(minutes=60), status=SlotStatusEnum.ACTIVE)
    slot2 = TimeSlot(service_id=cleaning.id, start_time=base + timedelta(hours=2), end_time=base + timedelta(hours=3), status=SlotStatusEnum.ACTIVE)
    slot3 = TimeSlot(service_id=repair.id, start_time=base + timedelta(days=1), end_time=base + timedelta(days=1, minutes=90), status=SlotStatusEnum.ACTIVE)
    slot4 = TimeSlot(service_id=repair.id, start_time=base + timedelta(days=1, hours=3), end_time=base + timedelta(days=1, hours=4, minutes=30), status=SlotStatusEnum.ACTIVE)
    session.add_all([slot1, slot2, slot3, slot4])
    session.flush()

    pending = Booking(
        customer_id=customer.id,
        provider_id=provider.id,
        service_id=cleaning.id,
        slot_id=slot1.id,
        status=BookingStatusEnum.PENDING,
        payment_status=PaymentStatusEnum.UNPAID,
        cancel_deadline=slot1.start_time - timedelta(hours=2),
    )
    confirmed = Booking(
        customer_id=customer.id,
        provider_id=provider.id,
        service_id=repair.id,
        slot_id=slot3.id,
        status=BookingStatusEnum.CONFIRMED,
        payment_status=PaymentStatusEnum.PAID,
        cancel_deadline=slot3.start_time - timedelta(hours=2),
        confirmed_at=datetime.utcnow(),
    )
    session.add_all([pending, confirmed])
    session.flush()

    payment = Payment(
        booking_id=confirmed.id,
        amount=repair.price,
        payment_reference="DEMO-PAID-001",
        status=PaymentStatusEnum.PAID,
        paid_at=datetime.utcnow(),
    )
    review = Review(
        booking_id=confirmed.id,
        customer_id=customer.id,
        provider_id=provider.id,
        service_id=repair.id,
        rating=5,
        comment="Great demo service.",
    )
    session.add_all([payment, review])
    session.flush()
