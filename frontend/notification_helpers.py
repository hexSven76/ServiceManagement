from typing import Any

from app.services.notification_service import NotificationService
from frontend.db_actions import get_actor, run_db_action
from frontend.ui_helpers import format_datetime


def notification_to_dict(notification) -> dict:
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "related_booking_id": notification.related_booking_id,
        "is_read": bool(notification.is_read),
        "created_at": notification.created_at,
        "created_at_text": format_datetime(notification.created_at),
    }


def fetch_notifications(user_id: int, unread_only: bool = False) -> list[dict]:
    def action(session):
        actor = get_actor(session, user_id)
        notifications = NotificationService(session).list_notifications(actor, unread_only=unread_only)
        return [notification_to_dict(n) for n in notifications]
    return run_db_action(action)


def fetch_unread_notification_count(user_id: int) -> int:
    def action(session):
        actor = get_actor(session, user_id)
        return NotificationService(session).unread_count(actor)
    return run_db_action(action)


def mark_notification_read(user_id: int, notification_id: int):
    def action(session):
        actor = get_actor(session, user_id)
        NotificationService(session).mark_read(actor, notification_id)
    return run_db_action(action)


def mark_all_notifications_read(user_id: int) -> int:
    def action(session):
        actor = get_actor(session, user_id)
        return NotificationService(session).mark_all_read(actor)
    return run_db_action(action)
