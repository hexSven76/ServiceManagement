import streamlit as st

from frontend.auth_ui import render_login_page
from frontend.customer_ui import render_customer_home
from frontend.provider_ui import render_provider_home
from frontend.admin_ui import render_admin_home
from frontend.session import logout_user


def render_navigation():
    if not st.session_state.is_logged_in:
        render_login_page()
        return

    st.sidebar.success(f"Logged in as: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        logout_user()
        st.rerun()

    role = st.session_state.role

    if role == "Admin":
        render_admin_home()
    elif role == "Provider":
        render_provider_home()
    elif role == "Customer":
        render_customer_home()
    else:
        st.error("Unknown user role.")