from __future__ import annotations
from datetime import datetime
from sqlalchemy import select, func
from ..exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from ..models import Booking, BookingStatusEnum, Review, RoleEnum, User
from .base import BaseService


class ReviewService(BaseService):
    def create_review(self, actor: User, booking_id: int, rating: int, comment: str | None = None) -> Review:
        if actor.role != RoleEnum.CUSTOMER:
            raise PermissionDeniedError("Only customers can review.")
        booking = self.session.get(Booking, booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")
        if booking.customer_id != actor.id:
            raise PermissionDeniedError("You can only review your own booking.")
        if booking.status != BookingStatusEnum.CONFIRMED:
            raise ValidationError("Booking must be confirmed before review.")
        if not (1 <= rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")

        existing = self.session.execute(select(Review).where(Review.booking_id == booking_id)).scalar_one_or_none()
        if existing:
            raise ConflictError("Review already exists for this booking.")

        review = Review(
            booking_id=booking_id,
            customer_id=actor.id,
            service_id=booking.service_id,
            provider_id=booking.provider_id,
            rating=rating,
            comment=comment,
            created_at=datetime.utcnow(),
        )
        self.session.add(review)
        self.session.flush()
        return review

    def list_reviews_for_service(self, service_id: int) -> list[Review]:
        return list(self.session.execute(select(Review).where(Review.service_id == service_id).order_by(Review.created_at.desc())).scalars().all())

    def list_reviews_for_provider(self, provider_id: int) -> list[Review]:
        return list(self.session.execute(select(Review).where(Review.provider_id == provider_id).order_by(Review.created_at.desc())).scalars().all())

    def list_all_reviews(self, actor: User) -> list[Review]:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can view all reviews.")
        return list(self.session.execute(select(Review).order_by(Review.created_at.desc())).scalars().all())

    def average_rating_for_service(self, service_id: int) -> float:
        avg = self.session.execute(select(func.avg(Review.rating)).where(Review.service_id == service_id)).scalar_one()
        return float(avg or 0.0)
