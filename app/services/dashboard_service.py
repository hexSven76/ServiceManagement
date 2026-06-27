from datetime import datetime, timedelta
from sqlalchemy import func

from app.models import Booking, Payment, RoleEnum, Service, ServiceStatusEnum, User
from app.services.base import BaseService


class DashboardService(BaseService):
    def admin_stats(self) -> dict:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = now - timedelta(days=7)
        users_by_role = {
            role.value: self.session.query(User).filter(User.role == role).count()
            for role in RoleEnum
        }
        services_by_status = {
            status.value: self.session.query(Service).filter(Service.status == status).count()
            for status in ServiceStatusEnum
        }
        top_services_rows = (
            self.session.query(Service.title, func.count(Booking.id).label("booking_count"))
            .join(Booking, Booking.service_id == Service.id, isouter=True)
            .group_by(Service.id)
            .order_by(func.count(Booking.id).desc())
            .limit(10)
            .all()
        )
        return {
            "total_users": self.session.query(User).count(),
            "total_bookings": self.session.query(Booking).count(),
            "today_bookings": self.session.query(Booking).filter(Booking.created_at >= today_start).count(),
            "week_bookings": self.session.query(Booking).filter(Booking.created_at >= week_start).count(),
            "total_services": self.session.query(Service).count(),
            "fake_income": float(self.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0),
            "users_by_role": users_by_role,
            "services_by_status": services_by_status,
            "top_services": [{"service": r.title, "bookings": int(r.booking_count)} for r in top_services_rows],
        }

    def provider_stats(self, provider_id: int) -> dict:
        bookings = self.session.query(Booking).filter(Booking.provider_id == provider_id).all()
        status_counts = {}
        for booking in bookings:
            status_counts[booking.status.value] = status_counts.get(booking.status.value, 0) + 1
        income = (
            self.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .join(Booking, Payment.booking_id == Booking.id)
            .filter(Booking.provider_id == provider_id)
            .scalar()
        )
        return {
            "total_services": self.session.query(Service).filter(Service.provider_id == provider_id).count(),
            "total_bookings": len(bookings),
            "booking_status_counts": status_counts,
            "fake_income": float(income or 0),
        }
