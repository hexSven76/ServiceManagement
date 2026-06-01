from __future__ import annotations
from app.db import init_db, get_session
from app.models import RoleEnum
from app.services import AuthService
from sqlalchemy import select, func
from app.models import User

def main():
    init_db()
    with get_session() as session:
        auth = AuthService(session)
        # Creating default admin if none exists
        exists = session.execute(select(func.count(User.id))).scalar_one()
        if exists == 0:
            auth.register(
                username="admin",
                email="admin@example.com",
                password="admin123",
                role=RoleEnum.ADMIN,
                full_name="System Admin",
            )

if __name__ == "__main__":
    main()
    print("Database initialized.")