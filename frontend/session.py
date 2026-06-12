import streamlit as st


def init_session():
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "role" not in st.session_state:
        st.session_state.role = None

    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False


def login_user(user_id: int, role: str):
    st.session_state.user_id = user_id
    st.session_state.role = role
    st.session_state.is_logged_in = True


def logout_user():
    st.session_state.user_id = None
    st.session_state.role = None
    st.session_state.is_logged_in = False