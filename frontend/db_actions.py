from typing import Callable, TypeVar

from sqlalchemy.orm import Session

from app.db import get_session
from app.models import User
from app.services.user_service import UserService

T = TypeVar("T")


def run_db_action(callback: Callable[[Session], T]) -> T:
    """
    Open one short-lived SQLAlchemy session for one Streamlit action/query.

    Rules:
    - Do not store ORM objects in st.session_state.
    - Return plain dict/list data from frontend helpers.
    - Let UI layer decide how to display errors.
    """
    with get_session() as session:
        try:
            return callback(session)
        except Exception:
            session.rollback()
            raise


def get_actor(session: Session, user_id: int) -> User:
    """
    Reload the current logged-in user inside the active DB session.
    """
    return UserService(session).get_user(user_id)


def enum_value(value):
    """
    Convert Python Enum values to plain strings for Streamlit tables/cards.
    """
    if value is None:
        return None

    if hasattr(value, "value"):
        return value.value

    return value