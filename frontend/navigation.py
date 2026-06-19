import streamlit as st

from frontend.auth_ui import render_login_page
from frontend.customer_ui import render_customer_page
from frontend.provider_ui import render_provider_page
from frontend.admin_ui import render_admin_page
from frontend.components import render_user_card
from frontend.session import logout_user


ADMIN_PAGES = [
    "Dashboard",
    "Users",
    "Services",
    "Bookings",
    "Reviews",
    "Reports",
]

PROVIDER_PAGES = [
    "Dashboard",
    "Profile",
    "My Services",
    "Schedule",
    "Bookings",
    "Reviews",
    "Reports",
]

CUSTOMER_PAGES = [
    "Browse Services",
    "My Bookings",
    "Profile",
    "Reviews",
    "Payments",
]


def render_navigation():
    if not st.session_state.is_logged_in:
        render_login_page()
        return

    role = st.session_state.role
    username = st.session_state.username

    st.sidebar.title("Service Booking")
    render_user_card(username=username, role=role)

    selected_page = get_selected_page(role)

    st.sidebar.markdown("---")

    if st.sidebar.button("Logout", use_container_width=True):
        logout_user()
        st.rerun()

    route_user(role, selected_page)


def get_selected_page(role: str) -> str:
    if role == "ADMIN":
        return st.sidebar.radio("Admin Menu", ADMIN_PAGES)

    if role == "PROVIDER":
        return st.sidebar.radio("Provider Menu", PROVIDER_PAGES)

    if role == "CUSTOMER":
        return st.sidebar.radio("Customer Menu", CUSTOMER_PAGES)

    return "Unknown"


def route_user(role: str, selected_page: str):
    if role == "ADMIN":
        render_admin_page(selected_page)
        return

    if role == "PROVIDER":
        render_provider_page(selected_page)
        return

    if role == "CUSTOMER":
        render_customer_page(selected_page)
        return

    st.error("Unknown user role.")