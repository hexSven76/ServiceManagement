from frontend.db_actions import get_actor, run_db_action
from app.services.user_service import UserService


def user_to_dict(user) -> dict:
    profile = user.profile
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "is_active": user.is_active,
        "created_at": user.created_at,
        "full_name": profile.full_name if profile else "",
        "phone": profile.phone if profile else "",
        "bio": profile.bio if profile else "",
    }


def fetch_my_profile(user_id: int) -> dict:
    def action(session):
        return user_to_dict(UserService(session).get_user(user_id))
    return run_db_action(action)


def update_my_profile(user_id: int, full_name: str, phone: str, bio: str) -> dict:
    def action(session):
        actor = get_actor(session, user_id)
        user = UserService(session).update_profile(actor, user_id, full_name, phone, bio)
        return user_to_dict(user)
    return run_db_action(action)
