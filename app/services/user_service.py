from __future__ import annotations
from sqlalchemy import select
from ..exceptions import NotFoundError, PermissionDeniedError, ValidationError
from ..models import Profile, RoleEnum, User
from .base import BaseService


class UserService(BaseService):
    def get_user(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    def update_profile(
        self,
        actor: User,
        target_user_id: int,
        full_name: str | None = None,
        phone: str | None = None,
        bio: str | None = None,
        image_path: str | None = None,
    ) -> User:
        target = self.get_user(target_user_id)
        if actor.role != RoleEnum.ADMIN and actor.id != target_user_id:
            raise PermissionDeniedError("You cannot edit this profile.")

        if not target.profile:
            target.profile = Profile(user_id=target.id)

        if full_name is not None:
            target.profile.full_name = full_name.strip() if full_name else None
        if phone is not None:
            target.profile.phone = phone.strip() if phone else None
        if bio is not None:
            target.profile.bio = bio.strip() if bio else None
        if image_path is not None:
            target.profile.image_path = image_path

        self.session.add(target)
        self.session.flush()
        return target

    def set_user_active(self, actor: User, user_id: int, active: bool) -> User:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can change user active status.")
        user = self.get_user(user_id)
        user.is_active = active
        self.session.add(user)
        self.session.flush()
        return user

    def change_role(self, actor: User, user_id: int, new_role: RoleEnum) -> User:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can change roles.")
        if new_role not in {RoleEnum.ADMIN, RoleEnum.PROVIDER, RoleEnum.CUSTOMER}:
            raise ValidationError("Invalid role.")
        user = self.get_user(user_id)
        user.role = new_role
        self.session.add(user)
        self.session.flush()
        return user

    def list_users(self, actor: User, role: RoleEnum | None = None) -> list[User]:
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admin can list all users.")
        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        return list(self.session.execute(stmt).scalars().all())
