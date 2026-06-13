from datetime import date, datetime, time
from typing import Any

from sqlalchemy import Date, DateTime, Time

from app.db import get_session
import app.models as models


def get_schedule_model():
    possible_names = [
        "Schedule",
        "TimeSlot",
        "Slot",
        "ScheduleSlot",
    ]

    for name in possible_names:
        if hasattr(models, name):
            return getattr(models, name)

    raise ImportError(
        "No schedule model found. Expected one of: Schedule, TimeSlot, Slot, ScheduleSlot."
    )


def get_model_columns(model_class) -> set[str]:
    return {column.name for column in model_class.__table__.columns}


def get_column(model_class, column_name: str):
    return model_class.__table__.columns.get(column_name)


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value

    return default


def get_first_existing_column(columns: set[str], possible_names: list[str]) -> str | None:
    for name in possible_names:
        if name in columns:
            return name

    return None


def normalize_datetime(value, fallback_date: date | None = None):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, time):
        if fallback_date is None:
            fallback_date = date.today()
        return datetime.combine(fallback_date, value)

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    return value


def schedule_to_dict(schedule) -> dict:
    schedule_model = type(schedule)
    columns = get_model_columns(schedule_model)

    slot_date = get_first_attr(
        schedule,
        ["date", "slot_date", "schedule_date", "day"],
        None,
    )

    raw_start = get_first_attr(
        schedule,
        ["start_time", "start_datetime", "starts_at", "start"],
        None,
    )

    raw_end = get_first_attr(
        schedule,
        ["end_time", "end_datetime", "ends_at", "end"],
        None,
    )

    start_datetime = normalize_datetime(raw_start, fallback_date=slot_date)
    end_datetime = normalize_datetime(raw_end, fallback_date=slot_date)

    service_id = get_first_attr(schedule, ["service_id"], None)

    provider_id = get_first_attr(schedule, ["provider_id"], None)

    is_active = get_first_attr(
        schedule,
        ["is_active", "active"],
        True,
    )

    is_booked = get_first_attr(
        schedule,
        ["is_booked", "booked"],
        False,
    )

    status = get_first_attr(
        schedule,
        ["status"],
        None,
    )

    return {
        "id": get_first_attr(schedule, ["id"], None),
        "service_id": service_id,
        "provider_id": provider_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "date": slot_date or (start_datetime.date() if start_datetime else None),
        "start_time": start_datetime.time() if isinstance(start_datetime, datetime) else None,
        "end_time": end_datetime.time() if isinstance(end_datetime, datetime) else None,
        "is_active": bool(is_active),
        "is_booked": bool(is_booked),
        "status": status,
        "raw_columns": columns,
    }


def set_datetime_field(
    data: dict,
    model_class,
    columns: set[str],
    possible_names: list[str],
    value: datetime,
):
    column_name = get_first_existing_column(columns, possible_names)

    if column_name is None:
        return

    column = get_column(model_class, column_name)

    if isinstance(column.type, Time):
        data[column_name] = value.time()
    elif isinstance(column.type, Date) and not isinstance(column.type, DateTime):
        data[column_name] = value.date()
    else:
        data[column_name] = value


def build_schedule_data(
    service_id: int,
    provider_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
    is_active: bool,
) -> dict:
    ScheduleModel = get_schedule_model()
    columns = get_model_columns(ScheduleModel)

    data = {}

    if "service_id" in columns:
        data["service_id"] = service_id

    if "provider_id" in columns:
        data["provider_id"] = provider_id

    date_field = get_first_existing_column(
        columns,
        ["date", "slot_date", "schedule_date", "day"],
    )

    if date_field:
        data[date_field] = start_datetime.date()

    set_datetime_field(
        data,
        ScheduleModel,
        columns,
        ["start_time", "start_datetime", "starts_at", "start"],
        start_datetime,
    )

    set_datetime_field(
        data,
        ScheduleModel,
        columns,
        ["end_time", "end_datetime", "ends_at", "end"],
        end_datetime,
    )

    if "is_active" in columns:
        data["is_active"] = is_active
    elif "active" in columns:
        data["active"] = is_active

    if "is_booked" in columns:
        data["is_booked"] = False
    elif "booked" in columns:
        data["booked"] = False

    if "status" in columns:
        data["status"] = "ACTIVE" if is_active else "INACTIVE"

    return data


def fetch_schedules_for_service(service_id: int) -> list[dict]:
    ScheduleModel = get_schedule_model()

    with get_session() as session:
        if hasattr(ScheduleModel, "service_id"):
            schedules = (
                session.query(ScheduleModel)
                .filter(ScheduleModel.service_id == service_id)
                .all()
            )
        else:
            schedules = session.query(ScheduleModel).all()

        return [schedule_to_dict(schedule) for schedule in schedules]


def fetch_schedules_for_provider_services(service_ids: list[int]) -> list[dict]:
    ScheduleModel = get_schedule_model()

    if not service_ids:
        return []

    with get_session() as session:
        if hasattr(ScheduleModel, "service_id"):
            schedules = (
                session.query(ScheduleModel)
                .filter(ScheduleModel.service_id.in_(service_ids))
                .all()
            )
        else:
            schedules = session.query(ScheduleModel).all()

        return [schedule_to_dict(schedule) for schedule in schedules]


def slots_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    return first_start < second_end and first_end > second_start


def validate_no_overlap(
    service_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
):
    existing_slots = fetch_schedules_for_service(service_id)

    for slot in existing_slots:
        existing_start = slot.get("start_datetime")
        existing_end = slot.get("end_datetime")

        if not existing_start or not existing_end:
            continue

        if not slot.get("is_active", True):
            continue

        if slots_overlap(
            start_datetime,
            end_datetime,
            existing_start,
            existing_end,
        ):
            raise ValueError(
                "This time slot overlaps with an existing active slot for this service."
            )


def create_schedule_slot(
    service_id: int,
    provider_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
    is_active: bool = True,
):
    if start_datetime >= end_datetime:
        raise ValueError("Start time must be before end time.")

    validate_no_overlap(
        service_id=service_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )

    ScheduleModel = get_schedule_model()

    with get_session() as session:
        schedule_data = build_schedule_data(
            service_id=service_id,
            provider_id=provider_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            is_active=is_active,
        )

        schedule = ScheduleModel(**schedule_data)

        session.add(schedule)
        session.commit()
        session.refresh(schedule)

        return schedule_to_dict(schedule)


def set_schedule_active_status(
    schedule_id: int,
    provider_service_ids: list[int],
    is_active: bool,
):
    ScheduleModel = get_schedule_model()

    with get_session() as session:
        schedule = session.get(ScheduleModel, schedule_id)

        if schedule is None:
            raise ValueError("Schedule slot not found.")

        schedule_service_id = getattr(schedule, "service_id", None)

        if schedule_service_id not in provider_service_ids:
            raise PermissionError("You cannot update another provider's schedule slot.")

        if hasattr(schedule, "is_active"):
            schedule.is_active = is_active
        elif hasattr(schedule, "active"):
            schedule.active = is_active
        else:
            raise ValueError("This schedule model has no active status field.")

        session.commit()
        session.refresh(schedule)

        return schedule_to_dict(schedule)


def delete_schedule_slot(schedule_id: int, provider_service_ids: list[int]):
    ScheduleModel = get_schedule_model()

    with get_session() as session:
        schedule = session.get(ScheduleModel, schedule_id)

        if schedule is None:
            raise ValueError("Schedule slot not found.")

        schedule_service_id = getattr(schedule, "service_id", None)

        if schedule_service_id not in provider_service_ids:
            raise PermissionError("You cannot delete another provider's schedule slot.")

        session.delete(schedule)
        session.commit()



def fetch_available_schedules_for_service(service_id: int) -> list[dict]:
    """
    Fetch only active and unbooked slots for one service.
    Used by the customer service detail page.
    """
    schedules = fetch_schedules_for_service(service_id)

    available_slots = []

    for slot in schedules:
        if not slot.get("is_active", False):
            continue

        if slot.get("is_booked", False):
            continue

        status = slot.get("status")

        if status is not None and status != "ACTIVE":
            continue

        available_slots.append(slot)

    available_slots.sort(
        key=lambda slot: slot.get("start_datetime")
    )

    return available_slots