from app.config import REPORT_DIR
from app.exceptions import NotFoundError, PermissionDeniedError
from app.models import Booking, Payment, RoleEnum, User
from app.services.base import BaseService
from app.services.dashboard_service import DashboardService
from app.utils.pdf_utils import simple_pdf


class ReportService(BaseService):
    def receipt_pdf(self, booking_id: int) -> str:
        booking = self.session.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found.")
        payment = self.session.query(Payment).filter(Payment.booking_id == booking.id).first()
        if payment is None:
            raise NotFoundError("Payment not found for this booking.")
        lines = [
            f"Receipt for Booking #{booking.id}",
            f"Customer: {booking.customer.username}",
            f"Provider: {booking.provider.username}",
            f"Service: {booking.service.title}",
            f"Slot: {booking.slot.start_time} - {booking.slot.end_time}",
            f"Amount: {payment.amount:,.0f} IRR",
            f"Payment reference: {payment.payment_reference or '-'}",
            f"Paid at: {payment.paid_at}",
        ]
        return simple_pdf(REPORT_DIR / f"receipt_booking_{booking.id}.pdf", "Payment Receipt", lines)

    def provider_bookings_pdf(self, provider_id: int) -> str:
        bookings = self.session.query(Booking).filter(Booking.provider_id == provider_id).order_by(Booking.created_at.desc()).all()
        lines = [
            f"Booking #{b.id} | {b.customer.username} | {b.service.title} | {b.status.value} | {b.payment_status.value} | {b.slot.start_time}"
            for b in bookings
        ] or ["No bookings found."]
        return simple_pdf(REPORT_DIR / f"provider_{provider_id}_bookings.pdf", "Provider Bookings", lines)

    def customer_bookings_pdf(self, customer_id: int) -> str:
        bookings = self.session.query(Booking).filter(Booking.customer_id == customer_id).order_by(Booking.created_at.desc()).all()
        lines = [
            f"Booking #{b.id} | {b.provider.username} | {b.service.title} | {b.status.value} | {b.payment_status.value} | {b.slot.start_time}"
            for b in bookings
        ] or ["No bookings found."]
        return simple_pdf(REPORT_DIR / f"customer_{customer_id}_bookings.pdf", "Customer Bookings", lines)

    def admin_stats_pdf(self) -> str:
        stats = DashboardService(self.session).admin_stats()
        lines = [
            f"Total users: {stats['total_users']}",
            f"Total bookings: {stats['total_bookings']}",
            f"Today bookings: {stats['today_bookings']}",
            f"Week bookings: {stats['week_bookings']}",
            f"Total services: {stats['total_services']}",
            f"Fake income: {stats['fake_income']:,.0f} IRR",
            f"Users by role: {stats['users_by_role']}",
            f"Services by status: {stats['services_by_status']}",
            f"Top services: {stats['top_services']}",
        ]
        return simple_pdf(REPORT_DIR / "admin_stats.pdf", "Admin Statistics", lines)
