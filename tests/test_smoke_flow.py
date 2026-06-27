from datetime import datetime, timedelta
from pathlib import Path

from app.db import get_session, init_db
from app.models import BookingStatusEnum, PaymentStatusEnum, User, Service, TimeSlot, Booking, Payment, Review
from app.seed import seed_demo_data
from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.report_service import ReportService
from app.services.review_service import ReviewService
from app.services.schedule_service import ScheduleService
from app.services.service_service import ServiceService


def test_seed_demo_data_is_available():
    init_db()
    with get_session() as session:
        seed_demo_data(session)
        assert session.query(User).count() >= 3
        assert session.query(Service).count() >= 2
        assert session.query(TimeSlot).count() >= 3
        assert session.query(Booking).count() >= 2
        assert session.query(Payment).count() >= 1
        assert session.query(Review).count() >= 1


def test_customer_provider_payment_receipt_review_flow():
    init_db()
    with get_session() as session:
        seed_demo_data(session)
        provider = AuthService(session).login("provider", "provider123")
        customer = AuthService(session).login("customer", "customer123")
        service = ServiceService(session).create_service(
            provider,
            provider.id,
            "Pytest Service",
            "Automated smoke-test service",
            "QA",
            30,
            100_000,
        )
        start = datetime.utcnow().replace(microsecond=0) + timedelta(days=14)
        slot = ScheduleService(session).create_slot(
            provider,
            service.id,
            start,
            start + timedelta(minutes=30),
        )
        booking = BookingService(session).create_booking(actor=customer, slot_id=slot.id)
        assert booking.status == BookingStatusEnum.PENDING

        BookingService(session).confirm_booking(provider, booking.id)
        payment = PaymentService(session).pay(customer, booking.id, "PYTEST")
        assert payment.status == PaymentStatusEnum.PAID

        review = ReviewService(session).create_review(customer, booking.id, 5, "Excellent")
        assert review.rating == 5

        receipt_path = ReportService(session).receipt_pdf(booking.id)
        assert Path(receipt_path).exists()
