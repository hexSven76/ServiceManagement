from typing import Any

from app.models import ServiceStatusEnum
from app.services.service_service import ServiceService
from frontend.db_actions import enum_value, get_actor, run_db_action


def get_first_attr(obj: Any, names: list[str], default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def normalize_service_status(status_value) -> str:
    raw = enum_value(status_value)

    if raw is None:
        return "ACTIVE"

    raw = str(raw).split(".")[-1].strip().upper()

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
            ["username", "email"],
            None,
        )

        profile = get_first_attr(provider, ["profile"], None)
        if profile is not None:
            provider_name = (
                get_first_attr(profile, ["full_name"], None)
                or provider_name
            )

    status = normalize_service_status(
        get_first_attr(service, ["status"], ServiceStatusEnum.ACTIVE)
    )

    return {
        "id": get_first_attr(service, ["id"]),
        "title": get_first_attr(service, ["title"], "Untitled Service"),
        "description": get_first_attr(service, ["description"], ""),
        "category": get_first_attr(service, ["category"], "Uncategorized"),
        "price": float(get_first_attr(service, ["price"], 0) or 0),
        "duration": get_first_attr(service, ["duration_minutes"], "-"),
        "duration_minutes": get_first_attr(service, ["duration_minutes"], None),
        "status": status,
        "is_active": status == "ACTIVE",  # compatibility for older UI code
        "image_path": get_first_attr(service, ["image_path"], None),
        "provider_id": get_first_attr(service, ["provider_id"], None),
        "provider_name": provider_name
        or f"Provider #{get_first_attr(service, ['provider_id'], '-')}",
    }


def fetch_all_services(
    actor_id: int | None = None,
    only_active: bool = False,
) -> list[dict]:
    """
    Fetch services through ServiceService.
    """
    def action(session):
        actor = get_actor(session, actor_id) if actor_id else None
        services = ServiceService(session).list_services(
            actor=actor,
            only_active=only_active,
        )
        return [service_to_dict(service) for service in services]

    return run_db_action(action)


def fetch_service_by_id(service_id: int) -> dict:
    """
    Fetch one service through ServiceService.
    """
    def action(session):
        service = ServiceService(session).get_service(service_id)
        return service_to_dict(service)

    return run_db_action(action)


def filter_services(
    services: list[dict],
    search_text: str = "",
    category: str = "All",
    provider: str = "All",
    min_price: float | int | None = None,
    max_price: float | int | None = None,
    active_only: bool = True,
) -> list[dict]:
    """
    Keep this frontend-side because Streamlit dynamic filters rerun immediately.
    Backend listing is still handled by ServiceService.
    """
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