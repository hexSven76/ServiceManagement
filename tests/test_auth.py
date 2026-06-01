from app.models import RoleEnum
from app.services.auth_service import AuthService

def test_register_and_login(session):
    auth = AuthService(session)
    user = auth.register("ali", "ali@example.com", "secret123", RoleEnum.CUSTOMER, full_name="Ali")
    assert user.id is not None
    logged = auth.login("ali", "secret123")
    assert logged.id == user.id
