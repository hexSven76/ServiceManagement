from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Date, DateTime, Time

from app.db import get_session
import app.models as models
from frontend.schedule_helpers import get_schedule_model, schedule_to_dict


def get_booking_model():
    possible_names = [
        "Booking",
        "Reservation",
    ]

    for name in possible_names:
        if hasattr(models, name):
            return getattr(models, name)

    raise ImportError("No booking model found. Expected Booking or Reservation.")


def get_model_columns(model_class) -> set[str]:
    return {column.name for column in model_class.__table__.columns}


def get_column(model_class, column_name: str):
    return model_class.__table__.columns.get(column_name)


def get_first_existing_column(columns: set[str], possible_names: list[str]) -> str | None:
    for name in possible_names:
        if name in columns:
            return name

    return None


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value

    return default


def enum_to_value(value):
    if value is not None and hasattr(value, "value"):
        return value.value

    return value


def get_enum_allowed_values(model_class, column_name: str) -> list[str]:
    column = get_column(model_class, column_name)

    if column is None:
        return []

    enum_values = getattr(column.type, "enums", None)

    if enum_values:
        return list(enum_values)

    enum_class = getattr(column.type, "enum_class", None)

    if enum_class is not None:
        return [member.name for member in enum_class]

    return []


def make_enum_value(model_class, column_name: str, desired_value: str):
    """
    Returns a safe value for SQLAlchemy Enum columns.
    If the column is mapped to a Python Enum class, return the Enum member.
    Otherwise return the string itself.
    """
    column = get_column(model_class, column_name)

    if column is None:
        return desired_value

    enum_class = getattr(column.type, "enum_class", None)

    if enum_class is not None:
        if desired_value in enum_class.__members__:
            return enum_class[desired_value]

        for member in enum_class:
            if str(member.value).upper() == desired_value.upper():
                return member

    return desired_value


def choose_enum_value(
    model_class,
    column_name: str,
    candidates: list[str],
    fallback: str,
):
    allowed_values = get_enum_allowed_values(model_class, column_name)

    if not allowed_values:
        return make_enum_value(model_class, column_name, fallback)

    allowed_upper_map = {
        str(value).upper(): str(value)
        for value in allowed_values
    }

    for candidate in candidates:
        candidate_upper = candidate.upper()

        if candidate_upper in allowed_upper_map:
            matched_value = allowed_upper_map[candidate_upper]
            return make_enum_value(model_class, column_name, matched_value)

    matched_fallback = allowed_upper_map.get(fallback.upper(), allowed_values[0])
    return make_enum_value(model_class, column_name, matched_fallback)


def set_first_existing_field(
    data: dict,
    columns: set[str],
    possible_names: list[str],
    value,
):
    for name in possible_names:
        if name in columns:
            data[name] = value
            return name

    return None


def set_datetime_field(
    data: dict,
    model_class,
    columns: set[str],
    possible_names: list[str],
    value: datetime | None,
):
    if value is None:
        return None

    column_name = get_first_existing_column(columns, possible_names)

    if column_name is None:
        return None

    column = get_column(model_class, column_name)

    if isinstance(column.type, Time):
        data[column_name] = value.time()
    elif isinstance(column.type, Date) and not isinstance(column.type, DateTime):
        data[column_name] = value.date()
    else:
        data[column_name] = value

    return column_name


def booking_to_dict(booking) -> dict:
    status = enum_to_value(
        get_first_attr(booking, ["status", "booking_status"], None)
    )

    payment_status = enum_to_value(
        get_first_attr(booking, ["payment_status", "payment_state"], None)
    )

    return {
        "id": get_first_attr(booking, ["id"], None),
        "customer_id": get_first_attr(booking, ["customer_id", "user_id"], None),
        "provider_id": get_first_attr(booking, ["provider_id"], None),
        "service_id": get_first_attr(booking, ["service_id"], None),
        "schedule_id": get_first_attr(
            booking,
            ["schedule_id", "slot_id", "time_slot_id", "schedule_slot_id"],
            None,
        ),
        "status": status,
        "payment_status": payment_status,
        "created_at": get_first_attr(
            booking,
            ["created_at", "booking_time", "created_on"],
            None,
        ),
    }


def build_booking_data(
    customer_id: int,
    provider_id: int,
    service_id: int,
    slot: dict,
    service: dict,
) -> dict:
    BookingModel = get_booking_model()
    columns = get_model_columns(BookingModel)

    data = {}

    set_first_existing_field(
        data,
        columns,
        ["customer_id", "user_id"],
        customer_id,
    )

    set_first_existing_field(
        data,
        columns,
        ["provider_id"],
        provider_id,
    )

    set_first_existing_field(
        data,
        columns,
        ["service_id"],
        service_id,
    )

    set_first_existing_field(
        data,
        columns,
        ["schedule_id", "slot_id", "time_slot_id", "schedule_slot_id"],
        slot.get("id"),
    )

    if "status" in columns:
        data["status"] = choose_enum_value(
            BookingModel,
            "status",
            candidates=["PENDING", "Pending", "pending"],
            fallback="PENDING",
        )

    elif "booking_status" in columns:
        data["booking_status"] = choose_enum_value(
            BookingModel,
            "booking_status",
            candidates=["PENDING", "Pending", "pending"],
            fallback="PENDING",
        )

    if "payment_status" in columns:
        data["payment_status"] = choose_enum_value(
            BookingModel,
            "payment_status",
            candidates=["UNPAID", "Unpaid", "unpaid"],
            fallback="UNPAID",
        )

    elif "payment_state" in columns:
        data["payment_state"] = choose_enum_value(
            BookingModel,
            "payment_state",
            candidates=["UNPAID", "Unpaid", "unpaid"],
            fallback="UNPAID",
        )

    if "is_paid" in columns:
        data["is_paid"] = False

    price = service.get("price")

    set_first_existing_field(
        data,
        columns,
        ["price", "total_price", "amount"],
        price,
    )

    start_datetime = slot.get("start_datetime")
    end_datetime = slot.get("end_datetime")
    
    if "cancel_deadline" in columns:
        if start_datetime is not None:
            data["cancel_deadline"] = start_datetime - timedelta(hours=2)
        else:
            data["cancel_deadline"] = datetime.now()

    set_datetime_field(
        data,
        BookingModel,
        columns,
        ["start_time", "start_datetime", "starts_at", "start"],
        start_datetime,
    )

    set_datetime_field(
        data,
        BookingModel,
        columns,
        ["end_time", "end_datetime", "ends_at", "end"],
        end_datetime,
    )

    set_datetime_field(
        data,
        BookingModel,
        columns,
        ["date", "booking_date"],
        start_datetime,
    )

    now = datetime.now()

    if "created_at" in columns:
        data["created_at"] = now

    if "updated_at" in columns:
        data["updated_at"] = now

    return data


def find_existing_booking_for_slot(session, slot_id: int):
    BookingModel = get_booking_model()
    columns = get_model_columns(BookingModel)

    slot_column_name = get_first_existing_column(
        columns,
        ["schedule_id", "slot_id", "time_slot_id", "schedule_slot_id"],
    )

    if slot_column_name is None:
        return None

    slot_column = getattr(BookingModel, slot_column_name)

    return (
        session.query(BookingModel)
        .filter(slot_column == slot_id)
        .first()
    )


def mark_schedule_as_booked(schedule):
    """
    Mark a slot as no longer available.

    Your backend may support:
    - is_booked / booked
    - status ACTIVE / INACTIVE
    """
    ScheduleModel = type(schedule)

    if hasattr(schedule, "is_booked"):
        schedule.is_booked = True

    elif hasattr(schedule, "booked"):
        schedule.booked = True

    if hasattr(schedule, "status"):
        schedule.status = choose_enum_value(
            ScheduleModel,
            "status",
            candidates=["INACTIVE", "Inactive", "inactive"],
            fallback="INACTIVE",
        )

    elif hasattr(schedule, "is_active"):
        schedule.is_active = False

    elif hasattr(schedule, "active"):
        schedule.active = False


def validate_slot_is_available(slot: dict):
    if not slot.get("is_active", False):
        raise ValueError("This time slot is not active.")

    if slot.get("is_booked", False):
        raise ValueError("This time slot is already booked.")

    status = slot.get("status")

    if status is not None and status != "ACTIVE":
        raise ValueError("This time slot is not available.")


def create_customer_booking(
    customer_id: int,
    service: dict,
    slot_id: int,
) -> dict:
    BookingModel = get_booking_model()
    ScheduleModel = get_schedule_model()

    with get_session() as session:
        schedule = session.get(ScheduleModel, slot_id)

        if schedule is None:
            raise ValueError("Selected time slot was not found.")

        slot = schedule_to_dict(schedule)

        if slot.get("service_id") != service.get("id"):
            raise ValueError("Selected slot does not belong to this service.")

        validate_slot_is_available(slot)

        existing_booking = find_existing_booking_for_slot(
            session=session,
            slot_id=slot_id,
        )

        if existing_booking is not None:
            raise ValueError("This time slot already has a booking.")

        provider_id = service.get("provider_id")

        if provider_id is None:
            provider_id = slot.get("provider_id")

        booking_data = build_booking_data(
            customer_id=customer_id,
            provider_id=provider_id,
            service_id=service.get("id"),
            slot=slot,
            service=service,
        )

        booking = BookingModel(**booking_data)

        session.add(booking)

        mark_schedule_as_booked(schedule)

        session.commit()
        session.refresh(booking)

        return booking_to_dict(booking)