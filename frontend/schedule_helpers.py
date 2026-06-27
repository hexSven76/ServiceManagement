from datetime import datetime

from app.exceptions import NotFoundError, PermissionDeniedError
from app.models import SlotStatusEnum, TimeSlot
from app.services.schedule_service import ScheduleService
from frontend.db_actions import enum_value, get_actor, run_db_action


def normalize_slot_status(status_value) -> str:
    raw = enum_value(status_value)

    if raw is None:
        return "ACTIVE"

    raw = str(raw).split(".")[-1].strip().upper()

    if raw in {"ACTIVE", "TRUE", "1"}:
        return "ACTIVE"

    if raw in {"INACTIVE", "FALSE", "0"}:
        return "INACTIVE"

    return raw


def slot_is_active(slot: dict) -> bool:
    return normalize_slot_status(slot.get("status")) == "ACTIVE"


def slot_to_dict(slot: TimeSlot) -> dict:
    status = normalize_slot_status(slot.status)

    return {
        "id": slot.id,
        "service_id": slot.service_id,
        "start_datetime": slot.start_time,
        "end_datetime": slot.end_time,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "status": status,
        "is_active": status == "ACTIVE",
        "is_booked": slot.booking is not None,
    }


def fetch_available_schedules_for_service(service_id: int) -> list[dict]:
    """
    Customer free slots.
    Uses ScheduleService.list_free_slots().
    """
    def action(session):
        slots = ScheduleService(session).list_free_slots(service_id)
        return [slot_to_dict(slot) for slot in slots]

    return run_db_action(action)


def fetch_schedules_for_provider_services(
    provider_service_ids: list[int],
) -> list[dict]:
    """
    Provider slot list.
    Uses ScheduleService.list_slots() for each provider service.
    """
    def action(session):
        schedule_service = ScheduleService(session)
        all_slots = []

        for service_id in provider_service_ids:
            if service_id is None:
                continue

            all_slots.extend(schedule_service.list_slots(service_id))

        return [slot_to_dict(slot) for slot in all_slots]

    return run_db_action(action)


def create_schedule_slot(
    service_id: int,
    provider_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
    is_active: bool = True,
):
    def action(session):
        actor = get_actor(session, provider_id)

        slot = ScheduleService(session).create_slot(
            actor=actor,
            service_id=service_id,
            start_time=start_datetime,
            end_time=end_datetime,
            status=SlotStatusEnum.ACTIVE if is_active else SlotStatusEnum.INACTIVE,
        )

        return slot_to_dict(slot)

    return run_db_action(action)


def get_slot_and_validate_provider_services(
    session,
    schedule_id: int,
    provider_service_ids: list[int],
) -> TimeSlot:
    slot = session.get(TimeSlot, schedule_id)

    if slot is None:
        raise NotFoundError("Time slot not found.")

    if slot.service_id not in provider_service_ids:
        raise PermissionDeniedError("You cannot manage another provider's slot.")

    return slot


def set_schedule_active_status(
    schedule_id: int,
    provider_service_ids: list[int],
    is_active: bool,
):
    """
    Kept same signature so provider_ui.py does not need a large rewrite.
    Internally it uses ScheduleService.toggle_slot_status().
    """
    def action(session):
        slot = get_slot_and_validate_provider_services(
            session=session,
            schedule_id=schedule_id,
            provider_service_ids=provider_service_ids,
        )

        actor = slot.service.provider

        updated_slot = ScheduleService(session).toggle_slot_status(
            actor=actor,
            slot_id=schedule_id,
            active=is_active,
        )

        return slot_to_dict(updated_slot)

    return run_db_action(action)


def delete_schedule_slot(
    schedule_id: int,
    provider_service_ids: list[int],
):
    """
    Kept same signature so provider_ui.py does not need a large rewrite.
    Internally it uses ScheduleService.delete_slot().
    """
    def action(session):
        slot = get_slot_and_validate_provider_services(
            session=session,
            schedule_id=schedule_id,
            provider_service_ids=provider_service_ids,
        )

        actor = slot.service.provider

        ScheduleService(session).delete_slot(
            actor=actor,
            slot_id=schedule_id,
        )

    return run_db_action(action)