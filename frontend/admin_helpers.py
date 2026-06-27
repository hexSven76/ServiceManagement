from app.models import BookingStatusEnum, RoleEnum, ServiceStatusEnum
from app.services.booking_service import BookingService
from app.services.dashboard_service import DashboardService
from app.services.review_service import ReviewService
from app.services.service_service import ServiceService
from app.services.user_service import UserService
from frontend.booking_helpers import booking_to_dict
from frontend.customer_review_helpers import review_to_dict
from frontend.db_actions import get_actor, run_db_action
from frontend.profile_helpers import user_to_dict
from frontend.service_helpers import service_to_dict


def fetch_admin_stats(admin_id: int) -> dict:
    def action(session):
        actor = get_actor(session, admin_id)
        if actor.role != RoleEnum.ADMIN:
            raise PermissionError("Only admins can view admin stats.")
        return DashboardService(session).admin_stats()
    return run_db_action(action)


def fetch_admin_users(admin_id: int) -> list[dict]:
    def action(session):
        actor = get_actor(session, admin_id)
        if actor.role != RoleEnum.ADMIN:
            raise PermissionError("Only admins can view users.")
        return [user_to_dict(user) for user in UserService(session).list_users()]
    return run_db_action(action)


def set_admin_user_active(admin_id: int, user_id: int, is_active: bool):
    def action(session):
        actor = get_actor(session, admin_id)
        return user_to_dict(UserService(session).set_user_active_status(actor, user_id, is_active))
    return run_db_action(action)


def change_admin_user_role(admin_id: int, user_id: int, role: str):
    def action(session):
        actor = get_actor(session, admin_id)
        return user_to_dict(UserService(session).change_user_role(actor, user_id, RoleEnum(role)))
    return run_db_action(action)


def fetch_admin_services(admin_id: int) -> list[dict]:
    def action(session):
        actor = get_actor(session, admin_id)
        if actor.role != RoleEnum.ADMIN:
            raise PermissionError("Only admins can view services.")
        return [service_to_dict(service) for service in ServiceService(session).list_services(actor=actor)]
    return run_db_action(action)


def update_admin_service_status(admin_id: int, service_id: int, status: str):
    def action(session):
        actor = get_actor(session, admin_id)
        service = ServiceService(session).update_service(actor, service_id, status=ServiceStatusEnum(status))
        return service_to_dict(service)
    return run_db_action(action)


def update_admin_service(
    admin_id: int,
    service_id: int,
    title: str,
    description: str,
    category: str,
    price: float,
    duration: int,
    status: str,
):
    def action(session):
        actor = get_actor(session, admin_id)
        service = ServiceService(session).update_service(
            actor=actor,
            service_id=service_id,
            title=title,
            description=description,
            category=category,
            duration_minutes=int(duration),
            price=float(price),
            status=ServiceStatusEnum(status),
        )
        return service_to_dict(service)

    return run_db_action(action)


def delete_admin_service(admin_id: int, service_id: int):
    def action(session):
        actor = get_actor(session, admin_id)
        ServiceService(session).delete_service(actor, service_id)
    return run_db_action(action)


def fetch_admin_bookings(admin_id: int) -> list[dict]:
    def action(session):
        actor = get_actor(session, admin_id)
        return [booking_to_dict(booking) for booking in BookingService(session).list_bookings_for_user(actor)]
    return run_db_action(action)


def force_confirm_admin_booking(admin_id: int, booking_id: int):
    def action(session):
        actor = get_actor(session, admin_id)
        return booking_to_dict(BookingService(session).confirm_booking(actor, booking_id))
    return run_db_action(action)


def force_cancel_admin_booking(admin_id: int, booking_id: int):
    def action(session):
        actor = get_actor(session, admin_id)
        return booking_to_dict(BookingService(session).cancel_booking(actor, booking_id, force=True))
    return run_db_action(action)


def fetch_admin_reviews(admin_id: int) -> list[dict]:
    def action(session):
        actor = get_actor(session, admin_id)
        if actor.role != RoleEnum.ADMIN:
            raise PermissionError("Only admins can view reviews.")
        return [review_to_dict(review) for review in ReviewService(session).list_all_reviews()]
    return run_db_action(action)
