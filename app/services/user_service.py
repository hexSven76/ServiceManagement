from app.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.models import RoleEnum, User, UserProfile
from app.services.base import BaseService


class UserService(BaseService):
    def get_user(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    def list_users(self, role: RoleEnum | str | None = None) -> list[User]:
        query = self.session.query(User).order_by(User.created_at.desc())
        if role:
            role_value = role if isinstance(role, RoleEnum) else RoleEnum(str(role).upper())
            query = query.filter(User.role == role_value)
        return query.all()

    def set_user_active_status(self, actor: User, user_id: int, is_active: bool) -> User:
        self._require_admin(actor)
        if actor.id == user_id and not is_active:
            raise ValidationError("You cannot deactivate your own admin account.")
        user = self.get_user(user_id)
        user.is_active = bool(is_active)
        self.session.flush()
        return user

    def change_user_role(self, actor: User, user_id: int, role: RoleEnum | str) -> User:
        self._require_admin(actor)
        if actor.id == user_id:
            raise ValidationError("You cannot change your own role.")
        user = self.get_user(user_id)
        user.role = role if isinstance(role, RoleEnum) else RoleEnum(str(role).upper())
        self.session.flush()
        return user

    def update_profile(
        self,
        actor: User,
        user_id: int,
        full_name: str | None = None,
        phone: str | None = None,
        bio: str | None = None,
    ) -> User:
        if actor.id != user_id and actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("You cannot edit another user's profile.")
        user = self.get_user(user_id)
        if user.profile is None:
            user.profile = UserProfile(user=user)
        user.profile.full_name = full_name
        user.profile.phone = phone
        user.profile.bio = bio
        self.session.flush()
        return user

    def _require_admin(self, actor: User):
        if actor.role != RoleEnum.ADMIN:
            raise PermissionDeniedError("Only admins can perform this action.")
