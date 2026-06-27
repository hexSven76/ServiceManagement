from datetime import timedelta

from sqlalchemy import and_

from app.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models import BookingStatusEnum, RoleEnum, Service, SlotStatusEnum, TimeSlot, User
from app.services.base import BaseService


class ScheduleService(BaseService):
    def get_slot(self, slot_id: int) -> TimeSlot:
        slot = self.session.get(TimeSlot, slot_id)
        if slot is None:
            raise NotFoundError("Time slot not found.")
        return slot

    def list_slots(self, service_id: int) -> list[TimeSlot]:
        return (
            self.session.query(TimeSlot)
            .filter(TimeSlot.service_id == service_id)
            .order_by(TimeSlot.start_time.asc())
            .all()
        )

    def list_free_slots(self, service_id: int) -> list[TimeSlot]:
        slots = (
            self.session.query(TimeSlot)
            .filter(
                TimeSlot.service_id == service_id,
                TimeSlot.status == SlotStatusEnum.ACTIVE,
            )
            .order_by(TimeSlot.start_time.asc())
            .all()
        )
        # A slot has a one-to-one booking history. Keep the frontend consistent
        # with the DB unique constraint by showing only never-booked slots.
        return [slot for slot in slots if slot.booking is None]

    def create_slot(
        self,
        actor: User,
        service_id: int,
        start_time,
        end_time,
        status: SlotStatusEnum = SlotStatusEnum.ACTIVE,
    ) -> TimeSlot:
        service = self.session.get(Service, service_id)
        if service is None:
            raise NotFoundError("Service not found.")
        self._can_manage(actor, service)
        self._validate_duration(service, start_time, end_time)
        self._validate_no_overlap(service_id, start_time, end_time)
        slot = TimeSlot(
            service_id=service_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        self.session.add(slot)
        self.session.flush()
        return slot

    def update_slot(self, actor: User, slot_id: int, start_time=None, end_time=None, status=None) -> TimeSlot:
        slot = self.get_slot(slot_id)
        self._can_manage(actor, slot.service)
        if slot.booking and slot.booking.status in {BookingStatusEnum.PENDING, BookingStatusEnum.CONFIRMED}:
            raise ValidationError("Booked slots cannot be edited.")
        new_start = start_time or slot.start_time
        new_end = end_time or slot.end_time
        self._validate_duration(slot.service, new_start, new_end)
        self._validate_no_overlap(slot.service_id, new_start, new_end, ignore_slot_id=slot.id)
        slot.start_time = new_start
        slot.end_time = new_end
        if status is not None:
            slot.status = status
        self.session.flush()
        return slot

    def toggle_slot_status(self, actor: User, slot_id: int, active: bool) -> TimeSlot:
        slot = self.get_slot(slot_id)
        self._can_manage(actor, slot.service)
        slot.status = SlotStatusEnum.ACTIVE if active else SlotStatusEnum.INACTIVE
        self.session.flush()
        return slot

    def delete_slot(self, actor: User, slot_id: int):
        slot = self.get_slot(slot_id)
        self._can_manage(actor, slot.service)
        if slot.booking:
            raise ValidationError("Cannot delete a slot with booking history. Deactivate it instead.")
        self.session.delete(slot)
        self.session.flush()

    def _can_manage(self, actor: User, service: Service):
        if actor.role == RoleEnum.ADMIN:
            return
        if actor.role == RoleEnum.PROVIDER and service.provider_id == actor.id:
            return
        raise PermissionDeniedError("You cannot manage this service schedule.")

    def _validate_duration(self, service: Service, start_time, end_time):
        if end_time <= start_time:
            raise ValidationError("End time must be after start time.")
        actual_minutes = int((end_time - start_time).total_seconds() // 60)
        if actual_minutes != int(service.duration_minutes):
            raise ValidationError("Slot duration must exactly match service duration.")

    def _validate_no_overlap(self, service_id: int, start_time, end_time, ignore_slot_id: int | None = None):
        query = self.session.query(TimeSlot).filter(
            TimeSlot.service_id == service_id,
            TimeSlot.start_time < end_time,
            TimeSlot.end_time > start_time,
        )
        if ignore_slot_id is not None:
            query = query.filter(TimeSlot.id != ignore_slot_id)
        if query.first():
            raise ValidationError("This slot overlaps with another slot for the same service.")
