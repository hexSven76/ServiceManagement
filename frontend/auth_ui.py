import streamlit as st

from app.db import get_session
from app.exceptions import AppError
from app.models import RoleEnum
from app.services.auth_service import AuthService
from frontend.session import login_user


def render_login_page():
    st.subheader("Welcome 👋")
    st.caption("Login or create an account to continue.")

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        render_login_form()

    with register_tab:
        render_register_form()


def render_login_form():
    with st.form("login_form"):
        identifier = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Login")

    if submitted:
        if not identifier or not password:
            st.warning("Please enter both username/email and password.")
            return

        try:
            with get_session() as session:
                auth_service = AuthService(session)
                user = auth_service.login(identifier=identifier, password=password)

                login_user(
                    user_id=user.id,
                    role=user.role.value,
                    username=user.username,
                )

            st.success("Login successful.")
            st.rerun()

        except AppError as error:
            st.error(str(error))
        except Exception as error:
            st.error("Unexpected error during login.")
            st.exception(error)


def render_register_form():
    with st.form("register_form"):
        username = st.text_input("Username", key="register_username")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm_password",
        )

        full_name = st.text_input("Full Name", key="register_full_name")
        phone = st.text_input("Phone", key="register_phone")
        bio = st.text_area("Bio", key="register_bio")

        role_label = st.selectbox(
            "Account Type",
            ["Customer", "Provider"],
        )

        submitted = st.form_submit_button("Create Account")

    if submitted:
        if not username or not email or not password:
            st.warning("Username, email, and password are required.")
            return

        if password != confirm_password:
            st.warning("Passwords do not match.")
            return

        role = RoleEnum.CUSTOMER if role_label == "Customer" else RoleEnum.PROVIDER

        try:
            with get_session() as session:
                auth_service = AuthService(session)
                user = auth_service.register(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    full_name=full_name or None,
                    phone=phone or None,
                    bio=bio or None,
                )

                login_user(
                    user_id=user.id,
                    role=user.role.value,
                    username=user.username,
                )

            st.success("Account created successfully.")
            st.rerun()

        except AppError as error:
            st.error(str(error))
        except Exception as error:
            st.error("Unexpected error during registration.")
            st.exception(error)