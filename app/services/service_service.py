from __future__ import annotations
from decimal import Decimal
from sqlalchemy import select, or_
from ..exceptions import NotFoundError, PermissionDeniedError, ValidationError
from ..models import RoleEnum, Service, ServiceStatusEnum, User
from .base import BaseService


class ServiceService(BaseService):
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
        if actor.role not in {RoleEnum.ADMIN, RoleEnum.PROVIDER}:
            raise PermissionDeniedError("Not allowed.")
        if actor.role == RoleEnum.PROVIDER and actor.id != provider_id:
            raise PermissionDeniedError("Providers can only create their own services.")
        if duration_minutes <= 0:
            raise ValidationError("Duration must be positive.")
        if price < 0:
            raise ValidationError("Price cannot be negative.")
        if not title.strip():
            raise ValidationError("Title is required.")

        service = Service(
            provider_id=provider_id,
            title=title.strip(),
            description=description,
            category=category.strip() if category else None,
            duration_minutes=duration_minutes,
            price=Decimal(str(price)),
            image_path=image_path,
            status=status,
        )
        self.session.add(service)
        self.session.flush()
        return service

    def get_service(self, service_id: int) -> Service:
        service = self.session.get(Service, service_id)
        if not service:
            raise NotFoundError("Service not found.")
        return service

    def update_service(self, actor: User, service_id: int, **fields) -> Service:
        service = self.get_service(service_id)
        if actor.role != RoleEnum.ADMIN and actor.id != service.provider_id:
            raise PermissionDeniedError("You cannot edit this service.")

        for key, value in fields.items():
            if value is None:
                continue
            if key == "title":
                if not str(value).strip():
                    raise ValidationError("Title cannot be empty.")
                service.title = str(value).strip()
            elif key == "description":
                service.description = value
            elif key == "category":
                service.category = str(value).strip() if value else None
            elif key == "duration_minutes":
                if int(value) <= 0:
                    raise ValidationError("Duration must be positive.")
                service.duration_minutes = int(value)
            elif key == "price":
                if float(value) < 0:
                    raise ValidationError("Price cannot be negative.")
                service.price = Decimal(str(value))
            elif key == "image_path":
                service.image_path = value
            elif key == "status":
                service.status = value
        self.session.add(service)
        self.session.flush()
        return service

    def delete_service(self, actor: User, service_id: int) -> None:
        service = self.get_service(service_id)
        if actor.role != RoleEnum.ADMIN and actor.id != service.provider_id:
            raise PermissionDeniedError("You cannot delete this service.")
        self.session.delete(service)
        self.session.flush()

    def list_services(
        self,
        actor: User | None = None,
        title: str | None = None,
        category: str | None = None,
        provider_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        status: ServiceStatusEnum | None = None,
        only_active: bool = False,
    ) -> list[Service]:
        stmt = select(Service)
        if title:
            stmt = stmt.where(Service.title.ilike(f"%{title.strip()}%"))
        if category:
            stmt = stmt.where(Service.category.ilike(f"%{category.strip()}%"))
        if provider_id is not None:
            stmt = stmt.where(Service.provider_id == provider_id)
        if min_price is not None:
            stmt = stmt.where(Service.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Service.price <= max_price)
        if status is not None:
            stmt = stmt.where(Service.status == status)
        if only_active:
            stmt = stmt.where(Service.status == ServiceStatusEnum.ACTIVE)
        return list(self.session.execute(stmt).scalars().all())
