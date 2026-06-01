from __future__ import annotations
from datetime import datetime
from sqlalchemy import select
from ..exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from ..models import BookingStatusEnum, NotificationTypeEnum, Booking, Payment, PaymentStatusEnum, RoleEnum, User
from .base import BaseService


class PaymentService(BaseService):
    def pay(self, actor: User, booking_id: int, payment_reference: str | None = None) -> Payment:
        booking = self.session.get(Booking, booking_id)

        if not booking:
            raise NotFoundError("Booking not found.")
        if actor.role not in {RoleEnum.CUSTOMER, RoleEnum.ADMIN}:
            raise PermissionDeniedError("Not allowed.")
        if actor.role == RoleEnum.CUSTOMER and actor.id != booking.customer_id:
            raise PermissionDeniedError("You can only pay for your own booking.")
        if booking.payment_status == PaymentStatusEnum.PAID:
            raise ConflictError("Booking is already paid.")
        if booking.status == BookingStatusEnum.CANCELED:
            raise ValidationError("Canceled booking cannot be paid.")

        existing = self.session.execute(select(Payment).where(Payment.booking_id == booking_id)).scalar_one_or_none()
        if existing:
            raise ConflictError("Payment already exists.")

        payment = Payment(
            booking_id=booking_id,
            amount=booking.service.price,
            payment_reference=payment_reference,
            status=PaymentStatusEnum.PAID,
            paid_at=datetime.utcnow(),
        )
        booking.payment_status = PaymentStatusEnum.PAID
        self.session.add_all([payment, booking])
        self.session.flush()
        return payment

    def get_payment(self, booking_id: int) -> Payment:
        payment = self.session.execute(select(Payment).where(Payment.booking_id == booking_id)).scalar_one_or_none()
        if not payment:
            raise NotFoundError("Payment not found.")
        return payment
