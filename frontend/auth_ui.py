import streamlit as st

from frontend.session import login_user


def render_login_page():
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # Temporary test login
        # Later we connect this to AuthService
        login_user(user_id=1, role="Admin")
        st.rerun()