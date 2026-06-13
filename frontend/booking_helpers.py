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


def fetch_customer_bookings(customer_id: int) -> list[dict]:
    BookingModel = get_booking_model()

    with get_session() as session:
        columns = get_model_columns(BookingModel)

        customer_column_name = get_first_existing_column(
            columns,
            ["customer_id", "user_id"],
        )

        if customer_column_name is None:
            raise ValueError("Booking model has no customer_id/user_id column.")

        customer_column = getattr(BookingModel, customer_column_name)

        bookings = (
            session.query(BookingModel)
            .filter(customer_column == customer_id)
            .order_by(BookingModel.id.desc())
            .all()
        )

        result = []

        for booking in bookings:
            booking_dict = booking_to_dict(booking)

            service = getattr(booking, "service", None)
            provider = getattr(booking, "provider", None)
            schedule = (
                getattr(booking, "schedule", None)
                or getattr(booking, "slot", None)
                or getattr(booking, "time_slot", None)
            )

            if service is not None:
                booking_dict["service_title"] = get_first_attr(
                    service,
                    ["title", "name", "service_name"],
                    f"Service #{booking_dict.get('service_id')}",
                )
                booking_dict["service_price"] = get_first_attr(
                    service,
                    ["price"],
                    None,
                )
            else:
                booking_dict["service_title"] = f"Service #{booking_dict.get('service_id')}"
                booking_dict["service_price"] = None

            if provider is not None:
                booking_dict["provider_name"] = get_first_attr(
                    provider,
                    ["username", "full_name", "email"],
                    f"Provider #{booking_dict.get('provider_id')}",
                )
            else:
                booking_dict["provider_name"] = f"Provider #{booking_dict.get('provider_id')}"

            if schedule is not None:
                slot = schedule_to_dict(schedule)
                booking_dict["slot_start"] = slot.get("start_datetime")
                booking_dict["slot_end"] = slot.get("end_datetime")
                booking_dict["slot_status"] = slot.get("status")
                booking_dict["slot_is_active"] = slot.get("is_active")
                booking_dict["slot_is_booked"] = slot.get("is_booked")
            else:
                booking_dict["slot_start"] = get_first_attr(
                    booking,
                    ["start_time", "start_datetime", "starts_at", "start"],
                    None,
                )
                booking_dict["slot_end"] = get_first_attr(
                    booking,
                    ["end_time", "end_datetime", "ends_at", "end"],
                    None,
                )

            booking_dict["cancel_deadline"] = get_first_attr(
                booking,
                ["cancel_deadline"],
                None,
            )

            booking_dict["confirmed_at"] = get_first_attr(
                booking,
                ["confirmed_at"],
                None,
            )

            booking_dict["rejected_at"] = get_first_attr(
                booking,
                ["rejected_at"],
                None,
            )

            booking_dict["canceled_at"] = get_first_attr(
                booking,
                ["canceled_at"],
                None,
            )

            result.append(booking_dict)

        return result


def can_customer_cancel_booking(booking: dict) -> tuple[bool, str]:
    status = str(booking.get("status") or "").upper()

    if status in ["CANCELED", "CANCELLED"]:
        return False, "This booking is already canceled."

    if status == "REJECTED":
        return False, "Rejected bookings cannot be canceled."

    cancel_deadline = booking.get("cancel_deadline")

    if cancel_deadline is None:
        return False, "This booking has no cancellation deadline."

    if datetime.now() > cancel_deadline:
        return False, "Cancellation deadline has passed."

    return True, "This booking can be canceled."


def cancel_customer_booking(
    booking_id: int,
    customer_id: int,
) -> dict:
    BookingModel = get_booking_model()

    with get_session() as session:
        booking = session.get(BookingModel, booking_id)

        if booking is None:
            raise ValueError("Booking not found.")

        booking_customer_id = get_first_attr(
            booking,
            ["customer_id", "user_id"],
            None,
        )

        if booking_customer_id != customer_id:
            raise PermissionError("You cannot cancel another customer's booking.")

        booking_dict = booking_to_dict(booking)

        booking_dict["cancel_deadline"] = get_first_attr(
            booking,
            ["cancel_deadline"],
            None,
        )

        can_cancel, reason = can_customer_cancel_booking(booking_dict)

        if not can_cancel:
            raise ValueError(reason)

        columns = get_model_columns(BookingModel)

        if "status" in columns:
            booking.status = choose_enum_value(
                BookingModel,
                "status",
                candidates=["CANCELED", "CANCELLED", "Canceled", "Cancelled"],
                fallback="CANCELED",
            )

        elif "booking_status" in columns:
            booking.booking_status = choose_enum_value(
                BookingModel,
                "booking_status",
                candidates=["CANCELED", "CANCELLED", "Canceled", "Cancelled"],
                fallback="CANCELED",
            )

        if "canceled_at" in columns:
            booking.canceled_at = datetime.now()

        if "updated_at" in columns:
            booking.updated_at = datetime.now()

        session.commit()
        session.refresh(booking)

        return booking_to_dict(booking)