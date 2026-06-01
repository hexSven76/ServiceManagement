from __future__ import annotations

from datetime import datetime
from sqlalchemy import select, and_

from ..exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from ..models import RoleEnum, Service, SlotStatusEnum, TimeSlot, User
from .base import BaseService


class ScheduleService(BaseService):
    def create_slot(self, actor: User, service_id: int, start_time: datetime, end_time: datetime, status: SlotStatusEnum = SlotStatusEnum.ACTIVE) -> TimeSlot:
        service = self.session.get(Service, service_id)
        if not service:
            raise NotFoundError("Service not found.")
        if actor.role != RoleEnum.ADMIN and actor.id != service.provider_id:
            raise PermissionDeniedError("You cannot manage this service schedule.")

        if end_time <= start_time:
            raise ValidationError("End time must be after start time.")
        duration_minutes = int((end_time - start_time).total_seconds() // 60)
        if duration_minutes != service.duration_minutes:
            raise ValidationError("Slot duration must exactly match service duration.")

        overlapping = self.session.execute(
            select(TimeSlot).where(
                TimeSlot.service_id == service_id,
                TimeSlot.start_time < end_time,
                TimeSlot.end_time > start_time,
            )
        ).scalar_one_or_none()
        if overlapping:
            raise ConflictError("This time slot overlaps with an existing slot.")

        slot = TimeSlot(
            service_id=service_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        self.session.add(slot)
        self.session.flush()
        return slot

    def update_slot(self, actor: User, slot_id: int, **fields) -> TimeSlot:
        slot = self.session.get(TimeSlot, slot_id)
        if not slot:
            raise NotFoundError("Time slot not found.")
        service = self.session.get(Service, slot.service_id)
        if actor.role != RoleEnum.ADMIN and actor.id != service.provider_id:
            raise PermissionDeniedError("You cannot edit this time slot.")

        new_start = fields.get("start_time", slot.start_time)
        new_end = fields.get("end_time", slot.end_time)
        new_status = fields.get("status", slot.status)

        if new_end <= new_start:
            raise ValidationError("End time must be after start time.")
        if int((new_end - new_start).total_seconds() // 60) != service.duration_minutes:
            raise ValidationError("Slot duration must exactly match service duration.")

        overlapping = self.session.execute(
            select(TimeSlot).where(
                TimeSlot.service_id == slot.service_id,
                TimeSlot.id != slot.id,
                TimeSlot.start_time < new_end,
                TimeSlot.end_time > new_start,
            )
        ).scalar_one_or_none()
        if overlapping:
            raise ConflictError("This time slot overlaps with an existing slot.")

        slot.start_time = new_start
        slot.end_time = new_end
        slot.status = new_status
        self.session.add(slot)
        self.session.flush()
        return slot

    def toggle_slot_status(self, actor: User, slot_id: int, active: bool) -> TimeSlot:
        slot = self.session.get(TimeSlot, slot_id)
        if not slot:
            raise NotFoundError("Time slot not found.")
        service = self.session.get(Service, slot.service_id)
        if actor.role != RoleEnum.ADMIN and actor.id != service.provider_id:
            raise PermissionDeniedError("You cannot edit this time slot.")
        slot.status = SlotStatusEnum.ACTIVE if active else SlotStatusEnum.INACTIVE
        self.session.add(slot)
        self.session.flush()
        return slot

    def delete_slot(self, actor: User, slot_id: int) -> None:
        slot = self.session.get(TimeSlot, slot_id)
        if not slot:
            raise NotFoundError("Time slot not found.")
        service = self.session.get(Service, slot.service_id)
        if actor.role != RoleEnum.ADMIN and actor.id != service.provider_id:
            raise PermissionDeniedError("You cannot delete this time slot.")
        self.session.delete(slot)
        self.session.flush()

    def list_slots(self, service_id: int, only_active: bool = False) -> list[TimeSlot]:
        stmt = select(TimeSlot).where(TimeSlot.service_id == service_id)
        if only_active:
            stmt = stmt.where(TimeSlot.status == SlotStatusEnum.ACTIVE)
        stmt = stmt.order_by(TimeSlot.start_time.asc())
        return list(self.session.execute(stmt).scalars().all())

    def list_free_slots(self, service_id: int) -> list[TimeSlot]:
        stmt = select(TimeSlot).where(
            TimeSlot.service_id == service_id,
            TimeSlot.status == SlotStatusEnum.ACTIVE,
            TimeSlot.booking == None,
            ).order_by(TimeSlot.start_time.asc())
        return list(self.session.execute(stmt).scalars().all())
