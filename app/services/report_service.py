from __future__ import annotations

from pathlib import Path
from sqlalchemy import select

from ..exceptions import PermissionDeniedError
from ..models import Booking, Payment, RoleEnum, User
from ..utils.pdf_utils import generate_pdf
from .base import BaseService


class ReportService(BaseService):
    def customer_bookings_pdf(self, actor: User, customer_id: int) -> str:
        if actor.role not in {RoleEnum.ADMIN, RoleEnum.CUSTOMER}:
            raise PermissionDeniedError("Not allowed.")
        if actor.role == RoleEnum.CUSTOMER and actor.id != customer_id:
            raise PermissionDeniedError("You can only export your own bookings.")

        bookings = list(self.session.execute(
            select(Booking).where(Booking.customer_id == customer_id).order_by(Booking.created_at.desc())
        ).scalars().all())
        rows = [
            [
                b.id,
                b.service.title,
                b.provider.username,
                b.slot.start_time.isoformat(sep=" ", timespec="minutes"),
                b.status.value,
                b.payment_status.value,
            ]
            for b in bookings
        ]
        return generate_pdf(
            filename=f"customer_{customer_id}_bookings.pdf",
            title="Customer Bookings Report",
            subtitle=f"Customer ID: {customer_id}",
            table_headers=["ID", "Service", "Provider", "Time", "Status", "Payment"],
            rows=rows,
        )

    def provider_bookings_pdf(self, actor: User, provider_id: int) -> str:
        if actor.role not in {RoleEnum.ADMIN, RoleEnum.PROVIDER}:
            raise PermissionDeniedError("Not allowed.")
        if actor.role == RoleEnum.PROVIDER and actor.id != provider_id:
            raise PermissionDeniedError("You can only export your own bookings.")

        bookings = list(self.session.execute(
            select(Booking).where(Booking.provider_id == provider_id).order_by(Booking.created_at.desc())
        ).scalars().all())
        rows = [
            [
                b.id,
                b.service.title,
                b.customer.username,
                b.slot.start_time.isoformat(sep=" ", timespec="minutes"),
                b.status.value,
                b.payment_status.value,
            ]
            for b in bookings
        ]
        return generate_pdf(
            filename=f"provider_{provider_id}_bookings.pdf",
            title="Provider Bookings Report",
            subtitle=f"Provider ID: {provider_id}",
            table_headers=["ID", "Service", "Customer", "Time", "Status", "Payment"],
            rows=rows,
        )

    def admin_stats_pdf(self, actor: User, stats: dict) -> str:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can export stats.")
        rows = []
        rows.append(["Total Users", stats.get("total_users", 0)])
        users_by_role = stats.get("users_by_role", {})
        rows.append(["Admins", users_by_role.get("ADMIN", 0)])
        rows.append(["Providers", users_by_role.get("PROVIDER", 0)])
        rows.append(["Customers", users_by_role.get("CUSTOMER", 0)])
        rows.append(["Total Services", stats.get("total_services", 0)])
        rows.append(["Active Services", stats.get("active_services", 0)])
        rows.append(["Inactive Services", stats.get("inactive_services", 0)])
        rows.append(["Total Bookings", stats.get("total_bookings", 0)])
        rows.append(["Bookings Today", stats.get("bookings_today", 0)])
        rows.append(["Bookings Week", stats.get("bookings_week", 0)])
        rows.append(["Fake Income", stats.get("fake_income", 0)])

        return generate_pdf(
            filename="admin_stats.pdf",
            title="Admin Statistics Report",
            subtitle="System-wide metrics",
            table_headers=["Metric", "Value"],
            rows=rows,
        )

    def receipt_pdf(self, actor: User, booking_id: int) -> str:
        booking = self.session.get(Booking, booking_id)
        if not booking:
            raise ValueError("Booking not found.")
        if actor.role == RoleEnum.CUSTOMER and actor.id != booking.customer_id:
            raise PermissionDeniedError("You can only export your own receipt.")
        if actor.role == RoleEnum.PROVIDER and actor.id != booking.provider_id:
            raise PermissionDeniedError("You can only export your own receipt.")

        payment = self.session.execute(select(Payment).where(Payment.booking_id == booking_id)).scalar_one_or_none()
        rows = [
            ["Booking ID", booking.id],
            ["Customer", booking.customer.username],
            ["Provider", booking.provider.username],
            ["Service", booking.service.title],
            ["Slot", booking.slot.start_time.isoformat(sep=" ", timespec="minutes")],
            ["Booking Status", booking.status.value],
            ["Payment Status", booking.payment_status.value],
            ["Amount", float(payment.amount) if payment else float(booking.service.price)],
            ["Payment Reference", payment.payment_reference if payment else "-"],
        ]
        return generate_pdf(
            filename=f"receipt_booking_{booking_id}.pdf",
            title="Payment Receipt",
            subtitle=f"Booking ID: {booking_id}",
            table_headers=["Field", "Value"],
            rows=rows,
        )
