from app.db import get_session, init_db
from app.seed import seed_demo_data


def main():
    init_db()
    with get_session() as session:
        seed_demo_data(session)
    print("Database is ready at data/service_booking.db")
    print("Demo accounts: admin/admin123, provider/provider123, customer/customer123")


if __name__ == "__main__":
    main()
