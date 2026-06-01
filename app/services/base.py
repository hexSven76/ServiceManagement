from __future__ import annotations
from sqlalchemy.orm import Session
from ..exceptions import ValidationError, NotFoundError, PermissionDeniedError, ConflictError

class BaseService:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _ensure(condition: bool, message: str, exc: type[Exception] = ValidationError) -> None:
        if not condition:
            raise exc(message)
