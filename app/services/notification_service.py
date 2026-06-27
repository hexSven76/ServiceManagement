from app.exceptions import NotFoundError, PermissionDeniedError
from app.models import Notification, RoleEnum, User
from app.services.base import BaseService


class NotificationService(BaseService):
    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        related_booking_id: int | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            related_booking_id=related_booking_id,
            is_read=False,
        )
        self.session.add(notification)
        self.session.flush()
        return notification

    def list_notifications(self, actor: User, unread_only: bool = False) -> list[Notification]:
        query = self.session.query(Notification).filter(Notification.user_id == actor.id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        return query.order_by(Notification.created_at.desc()).all()

    def unread_count(self, actor: User) -> int:
        return (
            self.session.query(Notification)
            .filter(Notification.user_id == actor.id, Notification.is_read.is_(False))
            .count()
        )

    def mark_read(self, actor: User, notification_id: int) -> Notification:
        notification = self.session.get(Notification, notification_id)
        if notification is None:
            raise NotFoundError("Notification not found.")
        if notification.user_id != actor.id and actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("You cannot update another user's notification.")
        notification.is_read = True
        self.session.flush()
        return notification

    def mark_all_read(self, actor: User) -> int:
        notifications = self.list_notifications(actor, unread_only=True)
        for notification in notifications:
            notification.is_read = True
        self.session.flush()
        return len(notifications)
