from typing import Any
from pathlib import Path

from app.services.payment_service import PaymentService
from frontend.db_actions import enum_value, get_actor, run_db_action
from app.services.report_service import ReportService


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def normalize_payment_status(value) -> str:
    raw = enum_value(value)

    if raw is None:
        return ""

    return str(raw).split(".")[-1].strip().upper()


def payment_to_dict(payment) -> dict:
    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": float(payment.amount or 0),
        "payment_reference": payment.payment_reference,
        "status": normalize_payment_status(payment.status),
        "paid_at": payment.paid_at,
    }


def pay_customer_booking(
    customer_id: int,
    booking_id: int,
    payment_reference: str | None = None,
) -> dict:
    """
    Mock payment action.

    Uses PaymentService.pay(), which:
    - creates a Payment row
    - marks payment as PAID
    - updates booking.payment_status to PAID
    """
    def action(session):
        actor = get_actor(session, customer_id)

        payment = PaymentService(session).pay(
            actor=actor,
            booking_id=booking_id,
            payment_reference=payment_reference or None,
        )

        session.commit()
        session.refresh(payment)

        return payment_to_dict(payment)

    return run_db_action(action)


def fetch_booking_payment(booking_id: int) -> dict | None:
    """
    Return payment data for an already-paid booking.
    """
    def action(session):
        try:
            payment = PaymentService(session).get_payment(booking_id)
        except Exception:
            return None

        return payment_to_dict(payment)

    return run_db_action(action)


def generate_customer_receipt_pdf(
    customer_id: int,
    booking_id: int,
) -> dict:
    """
    Generate receipt PDF for a paid customer booking.

    Returns:
    {
        "filename": "...",
        "bytes": b"..."
    }
    """
    def action(session):
        actor = get_actor(session, customer_id)

        receipt_path = ReportService(session).receipt_pdf(
            actor=actor,
            booking_id=booking_id,
        )

        path = Path(receipt_path)

        if not path.exists():
            raise FileNotFoundError(f"Receipt PDF was not generated: {receipt_path}")

        return {
            "filename": path.name,
            "bytes": path.read_bytes(),
        }

    return run_db_action(action)