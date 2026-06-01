from datetime import datetime, timedelta
from pathlib import Path
from app.models import RoleEnum
from app.services.auth_service import AuthService
from app.services.service_service import ServiceService
from app.services.schedule_service import ScheduleService
from app.services.booking_service import BookingService
from app.services.dashboard_service import DashboardService
from app.services.report_service import ReportService

def test_dashboard_and_report(session):
    auth = AuthService(session)
    admin = auth.register("admin", "admin@x.com", "secret123", RoleEnum.ADMIN)
    provider = auth.register("prov", "prov@x.com", "secret123", RoleEnum.PROVIDER)
    customer = auth.register("cust", "cust@x.com", "secret123", RoleEnum.CUSTOMER)
    service = ServiceService(session).create_service(provider, provider.id, "Consult", "desc", "General", 60, 150.0)
    slot = ScheduleService(session).create_slot(provider, service.id, datetime(2026, 1, 1, 12, 0), datetime(2026, 1, 1, 13, 0))
    booking = BookingService(session).create_booking(customer, slot.id)
    BookingService(session).confirm_booking(provider, booking.id)

    dash = DashboardService(session)
    stats = dash.admin_stats(admin)
    assert "total_users" in stats
    assert "top_services" in stats

    report = ReportService(session)
    path = report.admin_stats_pdf(admin, stats)
    assert Path(path).exists()
