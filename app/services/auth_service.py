from __future__ import annotations
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from ..exceptions import AuthenticationError, ConflictError, ValidationError
from ..models import Profile, RoleEnum, User
from ..security import hash_password, verify_password
from .base import BaseService


class AuthService(BaseService):
    def register(
        self,
        username: str,
        email: str,
        password: str,
        role: RoleEnum,
        full_name: str | None = None,
        phone: str | None = None,
        bio: str | None = None,
        image_path: str | None = None,
    ) -> User:
        username = username.strip()
        email = email.strip().lower()

        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        if "@" not in email:
            raise ValidationError("Invalid email.")
        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters.")
        if role not in {RoleEnum.ADMIN, RoleEnum.PROVIDER, RoleEnum.CUSTOMER}:
            raise ValidationError("Invalid role.")

        existing = self.session.execute(
            select(User).where(or_(User.username == username, User.email == email))
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("Username or email already exists.")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        user.profile = Profile(full_name=full_name, phone=phone, bio=bio, image_path=image_path)
        self.session.add(user)
        self.session.flush()
        return user

    def login(self, identifier: str, password: str) -> User:
        identifier = identifier.strip()
        user = self.session.execute(
            select(User).where(or_(User.username == identifier, User.email == identifier.lower()))
        ).scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials.")
        if not user.is_active:
            raise AuthenticationError("Account is inactive.")
        return user

    def change_password(self, user: User, old_password: str, new_password: str) -> User:
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationError("Old password is incorrect.")
        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters.")
        user.password_hash = hash_password(new_password)
        self.session.add(user)
        self.session.flush()
        return user
