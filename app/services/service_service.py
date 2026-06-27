from app.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models import RoleEnum, Service, ServiceStatusEnum, User
from app.services.base import BaseService


class ServiceService(BaseService):
    def get_service(self, service_id: int) -> Service:
        service = self.session.get(Service, service_id)
        if service is None:
            raise NotFoundError("Service not found.")
        return service

    def list_services(
        self,
        actor: User | None = None,
        only_active: bool = False,
        provider_id: int | None = None,
    ) -> list[Service]:
        query = self.session.query(Service)
        if provider_id is not None:
            query = query.filter(Service.provider_id == provider_id)
        elif actor is not None and actor.role == RoleEnum.PROVIDER:
            query = query.filter(Service.provider_id == actor.id)
        if only_active:
            query = query.filter(Service.status == ServiceStatusEnum.ACTIVE)
        return query.order_by(Service.created_at.desc()).all()

    def create_service(
        self,
        actor: User,
        provider_id: int,
        title: str,
        description: str | None,
        category: str | None,
        duration_minutes: int,
        price: float,
        image_path: str | None = None,
        status: ServiceStatusEnum = ServiceStatusEnum.ACTIVE,
    ) -> Service:
        if actor.role not in {RoleEnum.PROVIDER, RoleEnum.ADMIN}:
            raise PermissionDeniedError("Only providers can create services.")
        if actor.role == RoleEnum.PROVIDER and actor.id != provider_id:
            raise PermissionDeniedError("You cannot create services for another provider.")
        self._validate_service(title, duration_minutes, price)
        service = Service(
            provider_id=provider_id,
            title=title,
            description=description,
            category=category or "Uncategorized",
            duration_minutes=int(duration_minutes),
            price=float(price),
            image_path=image_path,
            status=status,
        )
        self.session.add(service)
        self.session.flush()
        return service

    def update_service(self, actor: User, service_id: int, **fields) -> Service:
        service = self.get_service(service_id)
        self._can_manage(actor, service)
        if "title" in fields or "duration_minutes" in fields or "price" in fields:
            self._validate_service(
                fields.get("title", service.title),
                fields.get("duration_minutes", service.duration_minutes),
                fields.get("price", service.price),
            )
        for key, value in fields.items():
            if value is not None and hasattr(service, key):
                setattr(service, key, value)
            elif key in {"description", "image_path"}:
                setattr(service, key, value)
        self.session.flush()
        return service

    def delete_service(self, actor: User, service_id: int):
        service = self.get_service(service_id)
        self._can_manage(actor, service)
        if service.bookings:
            raise ValidationError("Cannot delete a service with booking history. Deactivate it instead.")
        self.session.delete(service)
        self.session.flush()

    def _can_manage(self, actor: User, service: Service):
        if actor.role == RoleEnum.ADMIN:
            return
        if actor.role == RoleEnum.PROVIDER and service.provider_id == actor.id:
            return
        raise PermissionDeniedError("You cannot manage this service.")

    def _validate_service(self, title: str, duration_minutes: int, price: float):
        if not str(title or "").strip():
            raise ValidationError("Service title is required.")
        if int(duration_minutes or 0) <= 0:
            raise ValidationError("Service duration must be greater than zero.")
        if float(price or 0) < 0:
            raise ValidationError("Service price cannot be negative.")
