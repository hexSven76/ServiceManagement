from typing import Any

from app.db import get_session
from app.models import Service
from app.services.service_service import ServiceService


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def service_to_dict(service) -> dict:
    provider = get_first_attr(service, ["provider"], None)

    provider_name = None
    if provider is not None:
        provider_name = get_first_attr(provider, ["username", "full_name", "email"], None)

    return {
        "id": get_first_attr(service, ["id"]),
        "title": get_first_attr(service, ["title", "name", "service_name"], "Untitled Service"),
        "description": get_first_attr(service, ["description"], ""),
        "category": get_first_attr(service, ["category"], "Uncategorized"),
        "price": get_first_attr(service, ["price"], 0),
        "duration": get_first_attr(
            service,
            ["duration", "duration_minutes", "duration_time"],
            "-",
        ),
        "is_active": get_first_attr(service, ["is_active", "active"], True),
        "image_path": get_first_attr(service, ["image_path", "image"], None),
        "provider_id": get_first_attr(service, ["provider_id"], None),
        "provider_name": provider_name or f"Provider #{get_first_attr(service, ['provider_id'], '-')}",
    }


def fetch_all_services() -> list[dict]:
    """
    Fetch services from backend and convert them to plain dictionaries.

    Important:
    We convert ORM objects to dicts inside the DB session to avoid
    SQLAlchemy detached object issues after Streamlit reruns.
    """
    with get_session() as session:
        service_service = ServiceService(session)

        try:
            services = service_service.list_services()
        except TypeError:
            # Fallback if the backend method signature is different.
            services = session.query(Service).all()

        return [service_to_dict(service) for service in services]


def filter_services(
    services: list[dict],
    search_text: str = "",
    category: str = "All",
    provider: str = "All",
    min_price: float | int | None = None,
    max_price: float | int | None = None,
    active_only: bool = True,
) -> list[dict]:
    search_text = search_text.strip().lower()

    filtered = []

    for service in services:
        title = str(service.get("title", "")).lower()
        description = str(service.get("description", "")).lower()
        service_category = str(service.get("category", "")).lower()
        provider_name = str(service.get("provider_name", "")).lower()

        price = service.get("price") or 0
        is_active = bool(service.get("is_active", True))

        if active_only and not is_active:
            continue

        if search_text:
            searchable_text = " ".join(
                [title, description, service_category, provider_name]
            )

            if search_text not in searchable_text:
                continue

        if category != "All" and service.get("category") != category:
            continue

        if provider != "All" and service.get("provider_name") != provider:
            continue

        if min_price is not None and price < min_price:
            continue

        if max_price is not None and price > max_price:
            continue

        filtered.append(service)

    return filtered