from pathlib import Path

from app.services.report_service import ReportService
from frontend.db_actions import get_actor, run_db_action


def _read_report(path: str) -> bytes:
    return Path(path).read_bytes()


def receipt_pdf_bytes(booking_id: int) -> bytes:
    def action(session):
        path = ReportService(session).receipt_pdf(booking_id)
        return _read_report(path)
    return run_db_action(action)


def provider_bookings_pdf_bytes(provider_id: int) -> bytes:
    def action(session):
        path = ReportService(session).provider_bookings_pdf(provider_id)
        return _read_report(path)
    return run_db_action(action)


def customer_bookings_pdf_bytes(customer_id: int) -> bytes:
    def action(session):
        path = ReportService(session).customer_bookings_pdf(customer_id)
        return _read_report(path)
    return run_db_action(action)


def admin_stats_pdf_bytes(admin_id: int) -> bytes:
    def action(session):
        actor = get_actor(session, admin_id)
        if actor.role.value != "ADMIN":
            raise PermissionError("Only admins can export admin reports.")
        path = ReportService(session).admin_stats_pdf()
        return _read_report(path)
    return run_db_action(action)
