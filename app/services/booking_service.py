from datetime import datetime, timedelta

from app.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models import (
    Booking,
    BookingStatusEnum,
    PaymentStatusEnum,
    RoleEnum,
    ServiceStatusEnum,
    SlotStatusEnum,
    TimeSlot,
    User,
)
from app.services.base import BaseService
from app.services.notification_service import NotificationService


class BookingService(BaseService):
    def get_booking(self, booking_id: int) -> Booking:
        booking = self.session.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found.")
        return booking

    def create_booking(self, actor: User, slot_id: int) -> Booking:
        if actor.role != RoleEnum.CUSTOMER:
            raise PermissionDeniedError("Only customers can create bookings.")
        slot = self.session.get(TimeSlot, slot_id)
        if slot is None:
            raise NotFoundError("Selected slot was not found.")
        if slot.status != SlotStatusEnum.ACTIVE:
            raise ValidationError("Selected slot is inactive.")
        if slot.service.status != ServiceStatusEnum.ACTIVE:
            raise ValidationError("Selected service is inactive.")
        if slot.booking and slot.booking.status in {BookingStatusEnum.PENDING, BookingStatusEnum.CONFIRMED}:
            raise ValidationError("Selected slot is already booked.")
        cancel_deadline = slot.start_time - timedelta(hours=2)
        if cancel_deadline <= datetime.utcnow():
            cancel_deadline = datetime.utcnow() + timedelta(hours=1)
        booking = Booking(
            customer_id=actor.id,
            provider_id=slot.service.provider_id,
            service_id=slot.service_id,
            slot_id=slot.id,
            status=BookingStatusEnum.PENDING,
            payment_status=PaymentStatusEnum.UNPAID,
            cancel_deadline=cancel_deadline,
        )
        self.session.add(booking)
        self.session.flush()
        NotificationService(self.session).create_notification(
            user_id=booking.provider_id,
            title="New booking request",
            message=f"Booking #{booking.id} is waiting for your approval.",
            related_booking_id=booking.id,
        )
        return booking

    def list_bookings_for_user(self, actor: User) -> list[Booking]:
        query = self.session.query(Booking)
        if actor.role == RoleEnum.ADMIN:
            pass
        elif actor.role == RoleEnum.PROVIDER:
            query = query.filter(Booking.provider_id == actor.id)
        elif actor.role == RoleEnum.CUSTOMER:
            query = query.filter(Booking.customer_id == actor.id)
        else:
            raise PermissionDeniedError("Unknown role.")
        return query.order_by(Booking.created_at.desc()).all()

    def confirm_booking(self, actor: User, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        self._can_manage_provider_side(actor, booking)
        if booking.status != BookingStatusEnum.PENDING:
            raise ValidationError("Only pending bookings can be confirmed.")
        booking.status = BookingStatusEnum.CONFIRMED
        booking.confirmed_at = datetime.utcnow()
        NotificationService(self.session).create_notification(
            user_id=booking.customer_id,
            title="Booking confirmed",
            message=f"Booking #{booking.id} has been confirmed by the provider.",
            related_booking_id=booking.id,
        )
        self.session.flush()
        return booking

    def reject_booking(self, actor: User, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        self._can_manage_provider_side(actor, booking)
        if booking.status != BookingStatusEnum.PENDING:
            raise ValidationError("Only pending bookings can be rejected.")
        booking.status = BookingStatusEnum.REJECTED
        booking.rejected_at = datetime.utcnow()
        NotificationService(self.session).create_notification(
            user_id=booking.customer_id,
            title="Booking rejected",
            message=f"Booking #{booking.id} was rejected by the provider.",
            related_booking_id=booking.id,
        )
        self.session.flush()
        return booking

    def cancel_booking(self, actor: User, booking_id: int, force: bool = False) -> Booking:
        booking = self.get_booking(booking_id)
        if actor.role == RoleEnum.CUSTOMER and booking.customer_id != actor.id:
            raise PermissionDeniedError("You cannot cancel another customer's booking.")
        if actor.role == RoleEnum.PROVIDER and booking.provider_id != actor.id:
            raise PermissionDeniedError("You cannot cancel another provider's booking.")
        if actor.role not in {RoleEnum.CUSTOMER, RoleEnum.PROVIDER, RoleEnum.ADMIN}:
            raise PermissionDeniedError("You cannot cancel this booking.")
        if booking.status in {BookingStatusEnum.CANCELED, BookingStatusEnum.REJECTED}:
            raise ValidationError("This booking is already closed.")
        if not force and actor.role == RoleEnum.CUSTOMER and booking.cancel_deadline and datetime.utcnow() > booking.cancel_deadline:
            raise ValidationError("Cancellation deadline has passed.")
        booking.status = BookingStatusEnum.CANCELED
        booking.canceled_at = datetime.utcnow()
        target_user_id = booking.provider_id if actor.id == booking.customer_id else booking.customer_id
        NotificationService(self.session).create_notification(
            user_id=target_user_id,
            title="Booking canceled",
            message=f"Booking #{booking.id} has been canceled.",
            related_booking_id=booking.id,
        )
        self.session.flush()
        return booking

    def _can_manage_provider_side(self, actor: User, booking: Booking):
        if actor.role == RoleEnum.ADMIN:
            return
        if actor.role == RoleEnum.PROVIDER and booking.provider_id == actor.id:
            return
        raise PermissionDeniedError("You cannot manage this booking.")
