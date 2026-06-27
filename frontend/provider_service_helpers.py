from app.models import ServiceStatusEnum
from app.services.service_service import ServiceService
from frontend.db_actions import get_actor, run_db_action
from frontend.service_helpers import service_to_dict


def bool_to_service_status(is_active: bool) -> ServiceStatusEnum:
    return ServiceStatusEnum.ACTIVE if is_active else ServiceStatusEnum.INACTIVE


def fetch_provider_services(provider_id: int) -> list[dict]:
    def action(session):
        actor = get_actor(session, provider_id)
        services = ServiceService(session).list_services(
            actor=actor,
            provider_id=provider_id,
        )
        return [service_to_dict(service) for service in services]

    return run_db_action(action)


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
    def action(session):
        actor = get_actor(session, provider_id)
        service = ServiceService(session).create_service(
            actor=actor,
            provider_id=provider_id,
            title=title,
            description=description,
            category=category,
            duration_minutes=int(duration),
            price=float(price),
            image_path=image_path,
            status=bool_to_service_status(is_active),
        )
        return service_to_dict(service)

    return run_db_action(action)


def update_provider_service(
    service_id: int,
    provider_id: int,
    title: str,
    description: str,
    category: str,
    price: float,
    duration: int,
    is_active: bool,
    image_path: str | None = None,
):
    def action(session):
        actor = get_actor(session, provider_id)
        service = ServiceService(session).update_service(
            actor=actor,
            service_id=service_id,
            title=title,
            description=description,
            category=category,
            duration_minutes=int(duration),
            price=float(price),
            status=bool_to_service_status(is_active),
            image_path=image_path,
        )
        return service_to_dict(service)

    return run_db_action(action)


def set_provider_service_active_status(
    service_id: int,
    provider_id: int,
    is_active: bool,
):
    def action(session):
        actor = get_actor(session, provider_id)
        service = ServiceService(session).update_service(
            actor=actor,
            service_id=service_id,
            status=bool_to_service_status(is_active),
        )
        return service_to_dict(service)

    return run_db_action(action)


def delete_provider_service(service_id: int, provider_id: int):
    def action(session):
        actor = get_actor(session, provider_id)
        ServiceService(session).delete_service(
            actor=actor,
            service_id=service_id,
        )

    return run_db_action(action)