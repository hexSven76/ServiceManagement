import streamlit as st

from frontend.session import init_session
from frontend.navigation import render_navigation


st.set_page_config(
    page_title="Service Booking System",
    page_icon="📅",
    layout="wide"
)


def main():
    init_session()

    st.title("Service Booking and Management System")

    render_navigation()


if __name__ == "__main__":
    main()