from typing import Any

from app.db import get_session
from app.models import Service, ServiceStatusEnum
from frontend.service_helpers import service_to_dict


def get_model_columns(model_class) -> set[str]:
    return {column.name for column in model_class.__table__.columns}


def set_first_existing_field(
    data: dict,
    columns: set[str],
    possible_names: list[str],
    value: Any,
):
    for name in possible_names:
        if name in columns:
            data[name] = value
            return


def bool_to_service_status(is_active: bool) -> ServiceStatusEnum:
    return ServiceStatusEnum.ACTIVE if is_active else ServiceStatusEnum.INACTIVE


def build_service_data(
    provider_id: int,
    title: str,
    description: str,
    category: str,
    price: float,
    duration: int,
    is_active: bool,
    image_path: str | None = None,
) -> dict:
    columns = get_model_columns(Service)
    data = {}

    set_first_existing_field(data, columns, ["provider_id"], provider_id)
    set_first_existing_field(data, columns, ["title", "name", "service_name"], title)
    set_first_existing_field(data, columns, ["description"], description)
    set_first_existing_field(data, columns, ["category"], category)
    set_first_existing_field(data, columns, ["price"], price)

    # Backend model uses duration_minutes.
    set_first_existing_field(
        data,
        columns,
        ["duration_minutes", "duration", "duration_time"],
        duration,
    )

    # Correct backend field.
    if "status" in columns:
        data["status"] = bool_to_service_status(is_active)
    else:
        # Legacy fallback only.
        set_first_existing_field(data, columns, ["is_active", "active"], is_active)

    set_first_existing_field(data, columns, ["image_path", "image"], image_path)

    return data


def fetch_provider_services(provider_id: int) -> list[dict]:
    with get_session() as session:
        services = (
            session.query(Service)
            .filter(Service.provider_id == provider_id)
            .all()
        )
        return [service_to_dict(service) for service in services]


def create_provider_service(
    provider_id: int,
    title: str,
    description: str,
    category: str,
    price: float,
    duration: int,
    is_active: bool = True,
    image_path: str | None = None,
):
    with get_session() as session:
        service_data = build_service_data(
            provider_id=provider_id,
            title=title,
            description=description,
            category=category,
            price=price,
            duration=duration,
            is_active=is_active,
            image_path=image_path,
        )

        service = Service(**service_data)
        session.add(service)
        session.commit()
        session.refresh(service)

        return service_to_dict(service)


def update_provider_service(
    service_id: int,
    provider_id: int,
    title: str,
    description: str,
    category: str,
    price: float,
    duration: int,
    is_active: bool,
):
    with get_session() as session:
        service = session.get(Service, service_id)

        if service is None:
            raise ValueError("Service not found.")

        if service.provider_id != provider_id:
            raise PermissionError("You cannot edit another provider's service.")

        service_data = build_service_data(
            provider_id=provider_id,
            title=title,
            description=description,
            category=category,
            price=price,
            duration=duration,
            is_active=is_active,
        )

        for field, value in service_data.items():
            if field != "provider_id":
                setattr(service, field, value)

        session.commit()
        session.refresh(service)

        return service_to_dict(service)


def set_provider_service_active_status(
    service_id: int,
    provider_id: int,
    is_active: bool,
):
    with get_session() as session:
        service = session.get(Service, service_id)

        if service is None:
            raise ValueError("Service not found.")

        if service.provider_id != provider_id:
            raise PermissionError("You cannot update another provider's service.")

        if hasattr(service, "status"):
            service.status = bool_to_service_status(is_active)
        elif hasattr(service, "is_active"):
            service.is_active = is_active
        elif hasattr(service, "active"):
            service.active = is_active
        else:
            raise ValueError("This Service model has no status field.")

        session.commit()
        session.refresh(service)

        return service_to_dict(service)


def delete_provider_service(service_id: int, provider_id: int):
    with get_session() as session:
        service = session.get(Service, service_id)

        if service is None:
            raise ValueError("Service not found.")

        if service.provider_id != provider_id:
            raise PermissionError("You cannot delete another provider's service.")

        session.delete(service)
        session.commit()