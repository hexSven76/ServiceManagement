from typing import Any

from app.services.review_service import ReviewService
from frontend.db_actions import run_db_action
from frontend.ui_helpers import format_datetime


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def get_user_display_name(user) -> str:
    if user is None:
        return "Unknown customer"

    profile = get_first_attr(user, ["profile"], None)

    if profile is not None:
        full_name = get_first_attr(profile, ["full_name"], None)
        if full_name:
            return full_name

    return (
        get_first_attr(user, ["username"], None)
        or get_first_attr(user, ["email"], None)
        or f"Customer #{get_first_attr(user, ['id'], '-')}"
    )


def review_to_dict(review) -> dict:
    customer = get_first_attr(review, ["customer"], None)

    return {
        "id": review.id,
        "booking_id": review.booking_id,
        "customer_id": review.customer_id,
        "customer_name": get_user_display_name(customer),
        "service_id": review.service_id,
        "provider_id": review.provider_id,
        "rating": review.rating,
        "comment": review.comment or "",
        "created_at": review.created_at,
        "created_at_text": format_datetime(review.created_at),
    }


def fetch_service_review_summary(service_id: int) -> dict:
    """
    Return average rating, review count, and recent reviews for one service.
    """
    def action(session):
        review_service = ReviewService(session)

        average_rating = review_service.average_rating_for_service(service_id)
        reviews = review_service.list_reviews_for_service(service_id)

        review_dicts = [review_to_dict(review) for review in reviews]

        return {
            "average_rating": float(average_rating or 0),
            "review_count": len(review_dicts),
            "recent_reviews": review_dicts[:5],
        }

    return run_db_action(action)


def enrich_services_with_review_summary(services: list[dict]) -> list[dict]:
    """
    Add average_rating and review_count to service dictionaries.

    This is fine for the class demo scale. If the dataset becomes large,
    optimize later with one aggregate query instead of one query per service.
    """
    enriched_services = []

    for service in services:
        service_id = service.get("id")

        if not service_id:
            service["average_rating"] = 0.0
            service["review_count"] = 0
            enriched_services.append(service)
            continue

        summary = fetch_service_review_summary(service_id)

        service["average_rating"] = summary.get("average_rating", 0.0)
        service["review_count"] = summary.get("review_count", 0)

        enriched_services.append(service)

    return enriched_services


def format_rating(average_rating: float | int | None, review_count: int | None) -> str:
    try:
        rating = float(average_rating or 0)
    except (TypeError, ValueError):
        rating = 0.0

    count = int(review_count or 0)

    if count == 0:
        return "No reviews yet"

    return f"{rating:.1f}/5 ({count} review{'s' if count != 1 else ''})"