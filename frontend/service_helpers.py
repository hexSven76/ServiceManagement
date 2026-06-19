from typing import Any

from app.db import get_session
from app.models import Service, ServiceStatusEnum
from app.services.service_service import ServiceService


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def normalize_service_status(status_value) -> str:
    """
    Convert backend enum/string status into a stable frontend string.
    Output is always 'ACTIVE' or 'INACTIVE' when possible.
    """
    if status_value is None:
        return "ACTIVE"

    if hasattr(status_value, "value"):
        raw = str(status_value.value)
    else:
        raw = str(status_value)

    raw = raw.split(".")[-1].strip().upper()

    if raw in {"ACTIVE", "TRUE", "1"}:
        return "ACTIVE"

    if raw in {"INACTIVE", "FALSE", "0"}:
        return "INACTIVE"

    return raw


def service_is_active(service: dict) -> bool:
    return normalize_service_status(service.get("status")) == "ACTIVE"


def service_to_dict(service) -> dict:
    provider = get_first_attr(service, ["provider"], None)

    provider_name = None
    if provider is not None:
        provider_name = get_first_attr(
            provider,
            ["username", "full_name", "email"],
            None,
        )

    raw_status = get_first_attr(
        service,
        ["status"],
        ServiceStatusEnum.ACTIVE,
    )
    status = normalize_service_status(raw_status)

    return {
        "id": get_first_attr(service, ["id"]),
        "title": get_first_attr(
            service,
            ["title", "name", "service_name"],
            "Untitled Service",
        ),
        "description": get_first_attr(service, ["description"], ""),
        "category": get_first_attr(service, ["category"], "Uncategorized"),
        "price": get_first_attr(service, ["price"], 0),
        "duration": get_first_attr(
            service,
            ["duration_minutes", "duration", "duration_time"],
            "-",
        ),
        "status": status,
        # Compatibility field for old UI code.
        # This is derived from the real backend status, not from a DB column.
        "is_active": status == "ACTIVE",
        "image_path": get_first_attr(service, ["image_path", "image"], None),
        "provider_id": get_first_attr(service, ["provider_id"], None),
        "provider_name": provider_name
        or f"Provider #{get_first_attr(service, ['provider_id'], '-')}",
    }


def fetch_all_services() -> list[dict]:
    """
    Fetch services from backend and convert ORM objects to plain dictionaries
    inside the DB session.
    """
    with get_session() as session:
        service_service = ServiceService(session)

        try:
            services = service_service.list_services()
        except TypeError:
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

        if active_only and not service_is_active(service):
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


def find_service_by_id(services: list[dict], service_id: int) -> dict | None:
    for service in services:
        if service.get("id") == service_id:
            return service
    return None