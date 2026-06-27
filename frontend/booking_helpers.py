from datetime import datetime
from typing import Any

from app.models import BookingStatusEnum
from app.services.booking_service import BookingService
from frontend.db_actions import enum_value, get_actor, run_db_action


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def normalize_status(value) -> str:
    raw = enum_value(value)

    if raw is None:
        return ""

    return str(raw).split(".")[-1].strip().upper()


def user_display_name(user) -> str:
    if user is None:
        return "-"

    profile = get_first_attr(user, ["profile"], None)

    if profile is not None:
        full_name = get_first_attr(profile, ["full_name"], None)
        if full_name:
            return full_name

    return (
        get_first_attr(user, ["username"], None)
        or get_first_attr(user, ["email"], None)
        or f"User #{get_first_attr(user, ['id'], '-')}"
    )


def booking_to_dict(booking) -> dict:
    service = get_first_attr(booking, ["service"], None)
    provider = get_first_attr(booking, ["provider"], None)
    customer = get_first_attr(booking, ["customer"], None)
    slot = get_first_attr(booking, ["slot"], None)

    slot_start = get_first_attr(slot, ["start_time"], None) if slot else None
    slot_end = get_first_attr(slot, ["end_time"], None) if slot else None

    return {
        "id": booking.id,
        "customer_id": booking.customer_id,
        "provider_id": booking.provider_id,
        "service_id": booking.service_id,
        "slot_id": booking.slot_id,
        # compatibility with existing UI, which currently prints schedule_id
        "schedule_id": booking.slot_id,
        "status": normalize_status(booking.status),
        "payment_status": normalize_status(booking.payment_status),
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
        "confirmed_at": booking.confirmed_at,
        "rejected_at": booking.rejected_at,
        "canceled_at": booking.canceled_at,
        "cancel_deadline": booking.cancel_deadline,
        "service_title": (
            get_first_attr(service, ["title"], f"Service #{booking.service_id}")
            if service
            else f"Service #{booking.service_id}"
        ),
        "service_price": (
            float(get_first_attr(service, ["price"], 0) or 0)
            if service
            else None
        ),
        "provider_name": user_display_name(provider)
        if provider
        else f"Provider #{booking.provider_id}",
        "customer_name": user_display_name(customer)
        if customer
        else f"Customer #{booking.customer_id}",
        "customer_email": get_first_attr(customer, ["email"], "-")
        if customer
        else "-",
        "slot_start": slot_start,
        "slot_end": slot_end,
        "slot_status": normalize_status(get_first_attr(slot, ["status"], None))
        if slot
        else None,
    }


def create_customer_booking(
    customer_id: int,
    service: dict,
    slot_id: int,
) -> dict:
    """
    The service argument is kept for compatibility with customer_ui.py.
    Booking creation is now handled by BookingService.create_booking().
    """
    def action(session):
        actor = get_actor(session, customer_id)
        booking = BookingService(session).create_booking(
            actor=actor,
            slot_id=slot_id,
        )
        return booking_to_dict(booking)

    return run_db_action(action)


def fetch_customer_bookings(customer_id: int) -> list[dict]:
    def action(session):
        actor = get_actor(session, customer_id)
        bookings = BookingService(session).list_bookings_for_user(actor)
        return [booking_to_dict(booking) for booking in bookings]

    return run_db_action(action)


def can_customer_cancel_booking(booking: dict) -> tuple[bool, str]:
    status = str(booking.get("status") or "").upper()

    if status in {"CANCELED", "CANCELLED"}:
        return False, "This booking is already canceled."

    if status == "REJECTED":
        return False, "Rejected bookings cannot be canceled."

    cancel_deadline = booking.get("cancel_deadline")
    if cancel_deadline is None:
        return False, "This booking has no cancellation deadline."

    if datetime.utcnow() > cancel_deadline:
        return False, "Cancellation deadline has passed."

    return True, "This booking can be canceled."


def cancel_customer_booking(
    booking_id: int,
    customer_id: int,
) -> dict:
    def action(session):
        actor = get_actor(session, customer_id)
        booking = BookingService(session).cancel_booking(
            actor=actor,
            booking_id=booking_id,
            force=False,
        )
        return booking_to_dict(booking)

    return run_db_action(action)


def fetch_provider_bookings(provider_id: int) -> list[dict]:
    def action(session):
        actor = get_actor(session, provider_id)
        bookings = BookingService(session).list_bookings_for_user(actor)
        return [booking_to_dict(booking) for booking in bookings]

    return run_db_action(action)


def get_booking_status_upper(booking: dict) -> str:
    return str(booking.get("status") or "").upper()


def approve_provider_booking(
    booking_id: int,
    provider_id: int,
) -> dict:
    def action(session):
        actor = get_actor(session, provider_id)
        booking = BookingService(session).confirm_booking(
            actor=actor,
            booking_id=booking_id,
        )
        return booking_to_dict(booking)

    return run_db_action(action)


def reject_provider_booking(
    booking_id: int,
    provider_id: int,
) -> dict:
    def action(session):
        actor = get_actor(session, provider_id)
        booking = BookingService(session).reject_booking(
            actor=actor,
            booking_id=booking_id,
        )
        return booking_to_dict(booking)

    return run_db_action(action)


def cancel_provider_booking(
    booking_id: int,
    provider_id: int,
) -> dict:
    def action(session):
        actor = get_actor(session, provider_id)
        booking = BookingService(session).cancel_booking(
            actor=actor,
            booking_id=booking_id,
            force=False,
        )
        return booking_to_dict(booking)

    return run_db_action(action)


def is_booking_pending(booking: dict) -> bool:
    return get_booking_status_upper(booking) == BookingStatusEnum.PENDING.value