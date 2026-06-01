from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import func, select
from ..exceptions import PermissionDeniedError
from ..models import Booking, BookingStatusEnum, RoleEnum, Service, ServiceStatusEnum, User
from .base import BaseService


class DashboardService(BaseService):
    def admin_stats(self, actor: User) -> dict:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can view this dashboard.")

        total_users = self.session.execute(select(func.count(User.id))).scalar_one()
        provider_users = self.session.execute(select(func.count(User.id)).where(User.role == RoleEnum.PROVIDER)).scalar_one()
        customer_users = self.session.execute(select(func.count(User.id)).where(User.role == RoleEnum.CUSTOMER)).scalar_one()
        admin_users = self.session.execute(select(func.count(User.id)).where(User.role == RoleEnum.ADMIN)).scalar_one()

        total_services = self.session.execute(select(func.count(Service.id))).scalar_one()
        active_services = self.session.execute(select(func.count(Service.id)).where(Service.status == ServiceStatusEnum.ACTIVE)).scalar_one()
        inactive_services = self.session.execute(select(func.count(Service.id)).where(Service.status == ServiceStatusEnum.INACTIVE)).scalar_one()

        total_bookings = self.session.execute(select(func.count(Booking.id))).scalar_one()
        bookings_today = self.session.execute(
            select(func.count(Booking.id)).where(Booking.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
        ).scalar_one()
        bookings_week = self.session.execute(
            select(func.count(Booking.id)).where(Booking.created_at >= datetime.utcnow() - timedelta(days=7))
        ).scalar_one()

        top_services = self.session.execute(
            select(Service.title, func.count(Booking.id).label("cnt"))
            .join(Booking, Booking.service_id == Service.id)
            .group_by(Service.id)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
        ).all()

        income = self.session.execute(
            select(func.coalesce(func.sum(Service.price), 0))
            .select_from(Booking)
            .join(Service, Booking.service_id == Service.id)
            .where(Booking.status == BookingStatusEnum.CONFIRMED)
        ).scalar_one()

        return {
            "total_users": int(total_users),
            "users_by_role": {
                "ADMIN": int(admin_users),
                "PROVIDER": int(provider_users),
                "CUSTOMER": int(customer_users),
            },
            "total_services": int(total_services),
            "active_services": int(active_services),
            "inactive_services": int(inactive_services),
            "total_bookings": int(total_bookings),
            "bookings_today": int(bookings_today),
            "bookings_week": int(bookings_week),
            "top_services": [{"title": title, "count": int(cnt)} for title, cnt in top_services],
            "fake_income": float(income or 0),
        }

    def provider_stats(self, actor: User) -> dict:
        if actor.role != RoleEnum.PROVIDER:
            raise PermissionDeniedError("Only provider can view this dashboard.")

        total_services = self.session.execute(select(func.count(Service.id)).where(Service.provider_id == actor.id)).scalar_one()
        total_bookings = self.session.execute(select(func.count(Booking.id)).where(Booking.provider_id == actor.id)).scalar_one()
        status_counts = {
            status.value: int(self.session.execute(
                select(func.count(Booking.id)).where(Booking.provider_id == actor.id, Booking.status == status)
            ).scalar_one())
            for status in BookingStatusEnum
        }
        income = self.session.execute(
            select(func.coalesce(func.sum(Service.price), 0))
            .select_from(Booking)
            .join(Service, Booking.service_id == Service.id)
            .where(Booking.provider_id == actor.id, Booking.status == BookingStatusEnum.CONFIRMED)
        ).scalar_one()

        return {
            "total_services": int(total_services),
            "total_bookings": int(total_bookings),
            "booking_status_counts": status_counts,
            "fake_income": float(income or 0),
        }
