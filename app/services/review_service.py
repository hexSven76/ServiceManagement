from sqlalchemy import func

from app.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models import BookingStatusEnum, Review, RoleEnum, User
from app.services.base import BaseService
from app.services.booking_service import BookingService


class ReviewService(BaseService):
    def create_review(self, actor: User, booking_id: int, rating: int, comment: str | None = None) -> Review:
        booking = BookingService(self.session).get_booking(booking_id)
        if actor.role != RoleEnum.CUSTOMER or booking.customer_id != actor.id:
            raise PermissionDeniedError("You can only review your own bookings.")
        if booking.status not in {BookingStatusEnum.CONFIRMED, BookingStatusEnum.COMPLETED}:
            raise ValidationError("Only confirmed/completed bookings can be reviewed.")
        if booking.review is not None:
            raise ValidationError("You have already reviewed this booking.")
        if int(rating) < 1 or int(rating) > 5:
            raise ValidationError("Rating must be between 1 and 5.")
        review = Review(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            provider_id=booking.provider_id,
            service_id=booking.service_id,
            rating=int(rating),
            comment=comment,
        )
        self.session.add(review)
        self.session.flush()
        return review

    def get_review_for_booking(self, booking_id: int) -> Review | None:
        return self.session.query(Review).filter(Review.booking_id == booking_id).first()

    def list_reviews_for_service(self, service_id: int) -> list[Review]:
        return (
            self.session.query(Review)
            .filter(Review.service_id == service_id)
            .order_by(Review.created_at.desc())
            .all()
        )

    def list_reviews_for_provider(self, provider_id: int) -> list[Review]:
        return (
            self.session.query(Review)
            .filter(Review.provider_id == provider_id)
            .order_by(Review.created_at.desc())
            .all()
        )

    def list_reviews_for_customer(self, customer_id: int) -> list[Review]:
        return (
            self.session.query(Review)
            .filter(Review.customer_id == customer_id)
            .order_by(Review.created_at.desc())
            .all()
        )

    def list_all_reviews(self) -> list[Review]:
        return self.session.query(Review).order_by(Review.created_at.desc()).all()

    def average_rating_for_service(self, service_id: int) -> float:
        value = (
            self.session.query(func.avg(Review.rating))
            .filter(Review.service_id == service_id)
            .scalar()
        )
        return float(value or 0)
