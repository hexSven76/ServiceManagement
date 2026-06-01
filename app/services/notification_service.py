from __future__ import annotations
from sqlalchemy import select, func
from ..models import Notification, NotificationTypeEnum, User
from .base import BaseService


class NotificationService(BaseService):
    def create_notification(
        self,
        user_id: int,
        type: NotificationTypeEnum,
        title: str,
        message: str,
        related_booking_id: int | None = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            related_booking_id=related_booking_id,
            is_read=False,
        )
        self.session.add(notif)
        self.session.flush()
        return notif

    def list_notifications(self, user_id: int, unread_only: bool = False) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def mark_read(self, user_id: int, notification_id: int) -> Notification:
        notif = self.session.get(Notification, notification_id)
        if notif and notif.user_id == user_id:
            notif.is_read = True
            self.session.add(notif)
            self.session.flush()
        return notif

    def mark_all_read(self, user_id: int) -> int:
        notifications = self.session.execute(select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))).scalars().all()
        count = 0
        for n in notifications:
            n.is_read = True
            self.session.add(n)
            count += 1
        self.session.flush()
        return count

    def unread_count(self, user_id: int) -> int:
        return int(self.session.execute(
            select(func.count(Notification.id)).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        ).scalar_one())
