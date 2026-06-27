from datetime import datetime

from app.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models import BookingStatusEnum, Payment, PaymentStatusEnum, RoleEnum, User
from app.services.base import BaseService
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService


class PaymentService(BaseService):
    def pay(self, actor: User, booking_id: int, payment_reference: str | None = None) -> Payment:
        booking = BookingService(self.session).get_booking(booking_id)
        if actor.role == RoleEnum.CUSTOMER and booking.customer_id != actor.id:
            raise PermissionDeniedError("You cannot pay for another customer's booking.")
        if actor.role not in {RoleEnum.CUSTOMER, RoleEnum.ADMIN}:
            raise PermissionDeniedError("Only customers can pay for bookings.")
        if booking.status in {BookingStatusEnum.CANCELED, BookingStatusEnum.REJECTED}:
            raise ValidationError("Closed bookings cannot be paid.")
        if booking.payment_status == PaymentStatusEnum.PAID or booking.payment is not None:
            raise ValidationError("This booking has already been paid.")
        payment = Payment(
            booking_id=booking.id,
            amount=float(booking.service.price or 0),
            payment_reference=payment_reference,
            status=PaymentStatusEnum.PAID,
            paid_at=datetime.utcnow(),
        )
        booking.payment_status = PaymentStatusEnum.PAID
        self.session.add(payment)
        self.session.flush()
        NotificationService(self.session).create_notification(
            user_id=booking.customer_id,
            title="Payment received",
            message=f"Payment for booking #{booking.id} was recorded.",
            related_booking_id=booking.id,
        )
        NotificationService(self.session).create_notification(
            user_id=booking.provider_id,
            title="Booking paid",
            message=f"Customer paid for booking #{booking.id}.",
            related_booking_id=booking.id,
        )
        return payment

    def get_payment(self, booking_id: int) -> Payment:
        payment = self.session.query(Payment).filter(Payment.booking_id == booking_id).first()
        if payment is None:
            raise NotFoundError("Payment not found.")
        return payment
