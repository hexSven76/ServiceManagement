from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import select
from ..config import CANCEL_WINDOW_HOURS
from ..exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from ..models import (
    Booking,
    BookingStatusEnum,
    NotificationTypeEnum,
    PaymentStatusEnum,
    RoleEnum,
    ServiceStatusEnum,
    SlotStatusEnum,
    TimeSlot,
    User,
)
from .base import BaseService


class BookingService(BaseService):
    def create_booking(self, actor: User, slot_id: int) -> Booking:
        if actor.role != RoleEnum.CUSTOMER:
            raise PermissionDeniedError("Only customers can create bookings.")

        slot = self.session.get(TimeSlot, slot_id)
        if not slot:
            raise NotFoundError("Time slot not found.")
        if slot.status != SlotStatusEnum.ACTIVE:
            raise ValidationError("Time slot is not active.")
        if slot.booking is not None:
            raise ValidationError("Time slot already booked.")

        service = slot.service
        provider = service.provider
        if service.status != ServiceStatusEnum.ACTIVE or not provider.is_active:
            raise ValidationError("Service or provider is inactive.")

        cancel_deadline = slot.start_time - timedelta(hours=CANCEL_WINDOW_HOURS)
        booking = Booking(
            customer_id=actor.id,
            provider_id=provider.id,
            service_id=service.id,
            slot_id=slot.id,
            status=BookingStatusEnum.PENDING,
            payment_status=PaymentStatusEnum.UNPAID,
            cancel_deadline=cancel_deadline,
        )
        self.session.add(booking)
        self.session.flush()

        return booking  

    def get_booking(self, booking_id: int) -> Booking:
        booking = self.session.get(Booking, booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")
        return booking

    def confirm_booking(self, actor: User, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        if actor.role not in {RoleEnum.ADMIN, RoleEnum.PROVIDER}:
            raise PermissionDeniedError("Not allowed.")
        if actor.role == RoleEnum.PROVIDER and actor.id != booking.provider_id:
            raise PermissionDeniedError("You can only confirm your own bookings.")
        if booking.status != BookingStatusEnum.PENDING:
            raise ValidationError("Booking is not pending.")
        booking.status = BookingStatusEnum.CONFIRMED
        booking.confirmed_at = datetime.utcnow()
        self.session.add(booking)
        self.session.flush()
        return booking

    def reject_booking(self, actor: User, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        if actor.role not in {RoleEnum.ADMIN, RoleEnum.PROVIDER}:
            raise PermissionDeniedError("Not allowed.")
        if actor.role == RoleEnum.PROVIDER and actor.id != booking.provider_id:
            raise PermissionDeniedError("You can only reject your own bookings.")
        if booking.status != BookingStatusEnum.PENDING:
            raise ValidationError("Booking is not pending.")
        booking.status = BookingStatusEnum.REJECTED
        booking.rejected_at = datetime.utcnow()
        self.session.add(booking)
        self.session.flush()
        return booking

    def cancel_booking(self, actor: User, booking_id: int, force: bool = False) -> Booking:
        booking = self.get_booking(booking_id)

        allowed = actor.role == RoleEnum.ADMIN or actor.id in {booking.customer_id, booking.provider_id}
        if not allowed:
            raise PermissionDeniedError("Not allowed.")

        now = datetime.utcnow()
        if not force and actor.role == RoleEnum.CUSTOMER and now > booking.cancel_deadline:
            raise ValidationError("Cancellation deadline has passed.")

        if booking.status in {BookingStatusEnum.CANCELED, BookingStatusEnum.REJECTED}:
            raise ValidationError("Booking is already closed.")

        booking.status = BookingStatusEnum.CANCELED
        booking.canceled_at = now
        self.session.add(booking)
        self.session.flush()
        return booking

    def list_bookings_for_user(self, actor: User, target_user_id: int | None = None) -> list[Booking]:
        if target_user_id is None:
            target_user_id = actor.id

        if actor.role == RoleEnum.ADMIN:
            stmt = select(Booking)
        elif actor.role == RoleEnum.PROVIDER:
            stmt = select(Booking).where(Booking.provider_id == actor.id)
        else:
            if target_user_id != actor.id:
                raise PermissionDeniedError("You can only view your own bookings.")
            stmt = select(Booking).where(Booking.customer_id == actor.id)

        stmt = stmt.order_by(Booking.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def force_approve(self, actor: User, booking_id: int) -> Booking:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can force approve.")
        booking = self.get_booking(booking_id)
        booking.status = BookingStatusEnum.CONFIRMED
        booking.confirmed_at = datetime.utcnow()
        self.session.add(booking)
        self.session.flush()
        return booking

    def force_cancel(self, actor: User, booking_id: int) -> Booking:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can force cancel.")
        return self.cancel_booking(actor, booking_id, force=True)

    def auto_expire_cancellations(self) -> int:
        now = datetime.utcnow()
        stmt = select(Booking).where(
            Booking.status == BookingStatusEnum.PENDING,
            Booking.cancel_deadline < now,
        )
        bookings = list(self.session.execute(stmt).scalars().all())
        for booking in bookings:
            booking.status = BookingStatusEnum.CANCELED
            booking.canceled_at = now
            self.session.add(booking)
        self.session.flush()
        return len(bookings)
