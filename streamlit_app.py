import streamlit as st

from app.db import get_session, init_db
from app.seed import seed_demo_data
from frontend.session import init_session
from frontend.navigation import render_navigation


st.set_page_config(
    page_title="Service Booking System",
    page_icon="📅",
    layout="wide"
)


def main():
    init_db()
    with get_session() as session:
        seed_demo_data(session)
    init_session()

    st.title("Service Booking and Management System")

    render_navigation()


if __name__ == "__main__":
    main()