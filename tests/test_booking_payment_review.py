from datetime import datetime, timedelta
import pytest
from app.models import RoleEnum, BookingStatusEnum, PaymentStatusEnum
from app.services.auth_service import AuthService
from app.services.service_service import ServiceService
from app.services.schedule_service import ScheduleService
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.review_service import ReviewService

def setup_flow(session):
    auth = AuthService(session)
    provider = auth.register("prov", "prov@example.com", "secret123", RoleEnum.PROVIDER)
    customer = auth.register("cust", "cust@example.com", "secret123", RoleEnum.CUSTOMER)
    service = ServiceService(session).create_service(provider, provider.id, "Consult", "desc", "General", 60, 150.0)
    slot = ScheduleService(session).create_slot(
        provider, service.id, datetime(2026, 1, 1, 12, 0), datetime(2026, 1, 1, 13, 0)
    )
    return provider, customer, service, slot

def test_booking_payment_review(session):
    provider, customer, service, slot = setup_flow(session)
    booking_service = BookingService(session)
    booking = booking_service.create_booking(customer, slot.id)
    assert booking.status == BookingStatusEnum.PENDING

    booking_service.confirm_booking(provider, booking.id)

    payment = PaymentService(session).pay(customer, booking.id, "REF-001")
    assert payment.status == PaymentStatusEnum.PAID

    review = ReviewService(session).create_review(customer, booking.id, 5, "Great")
    assert review.rating == 5

def test_double_payment_rejected(session):
    provider, customer, service, slot = setup_flow(session)
    booking_service = BookingService(session)
    booking = booking_service.create_booking(customer, slot.id)
    PaymentService(session).pay(customer, booking.id, "REF-001")
    with pytest.raises(Exception):
        PaymentService(session).pay(customer, booking.id, "REF-002")
