from sqlalchemy import or_

from app.exceptions import AuthenticationError, ValidationError
from app.models import RoleEnum, User, UserProfile
from app.security import hash_password, verify_password
from app.services.base import BaseService


class AuthService(BaseService):
    def login(self, identifier: str, password: str) -> User:
        user = (
            self.session.query(User)
            .filter(or_(User.username == identifier, User.email == identifier))
            .first()
        )
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username/email or password.")
        if not user.is_active:
            raise AuthenticationError("This account is inactive.")
        return user

    def register(
        self,
        username: str,
        email: str,
        password: str,
        role: RoleEnum,
        full_name: str | None = None,
        phone: str | None = None,
        bio: str | None = None,
    ) -> User:
        if role == RoleEnum.ADMIN:
            raise ValidationError("Admin accounts must be created by the system.")
        if self.session.query(User).filter(User.username == username).first():
            raise ValidationError("Username already exists.")
        if self.session.query(User).filter(User.email == email).first():
            raise ValidationError("Email already exists.")
        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        user.profile = UserProfile(full_name=full_name, phone=phone, bio=bio)
        self.session.add(user)
        self.session.flush()
        return user
