import streamlit as st

from frontend.auth_ui import render_login_page
from frontend.customer_ui import render_customer_page
from frontend.provider_ui import render_provider_page
from frontend.admin_ui import render_admin_page
from frontend.components import render_user_card
from frontend.help_ui import render_help_page
from frontend.notification_helpers import (
    fetch_notifications,
    fetch_unread_notification_count,
    mark_all_notifications_read,
    mark_notification_read,
)
from frontend.session import logout_user
from frontend.ui_helpers import show_action_error


ADMIN_PAGES = [
    "Dashboard",
    "Users",
    "Services",
    "Bookings",
    "Reviews",
    "Reports",
    "Help/About",
]

PROVIDER_PAGES = [
    "Dashboard",
    "Profile",
    "My Services",
    "Schedule",
    "Bookings",
    "Reviews",
    "Reports",
    "Help/About",
]

CUSTOMER_PAGES = [
    "Browse Services",
    "My Bookings",
    "Profile",
    "Reviews",
    "Payments",
    "Help/About",
]


def render_navigation():
    if not st.session_state.is_logged_in:
        render_login_page()
        return

    role = st.session_state.role
    username = st.session_state.username

    st.sidebar.title("Service Booking")
    render_user_card(username=username, role=role)
    render_notification_panel()

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
    if selected_page == "Help/About":
        render_help_page()
        return

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


def render_notification_panel():
    user_id = st.session_state.user_id
    if not user_id:
        return

    try:
        unread_count = fetch_unread_notification_count(user_id)
    except Exception:
        unread_count = 0

    with st.sidebar.expander(f"Notifications ({unread_count} unread)", expanded=False):
        unread_only = st.checkbox("Unread only", value=False, key="notifications_unread_only")
        if st.button("Refresh", use_container_width=True, key="refresh_notifications"):
            st.rerun()
        try:
            notifications = fetch_notifications(user_id, unread_only=unread_only)
        except Exception as error:
            show_action_error(error)
            return

        if not notifications:
            st.caption("No notifications.")
            return

        if st.button("Mark all as read", use_container_width=True, key="mark_all_notifications_read"):
            try:
                mark_all_notifications_read(user_id)
                st.rerun()
            except Exception as error:
                show_action_error(error)

        for notification in notifications[:10]:
            status = "●" if not notification.get("is_read") else "○"
            st.markdown(f"**{status} {notification.get('title')}**")
            st.caption(notification.get("created_at_text"))
            st.write(notification.get("message"))
            if not notification.get("is_read"):
                if st.button("Mark read", key=f"mark_notification_{notification.get('id')}", use_container_width=True):
                    try:
                        mark_notification_read(user_id, notification.get("id"))
                        st.rerun()
                    except Exception as error:
                        show_action_error(error)
            st.markdown("---")
