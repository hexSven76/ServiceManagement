import streamlit as st

from frontend.components import page_title, placeholder_page


def render_admin_page(selected_page: str):
    if selected_page == "Dashboard":
        render_admin_dashboard()

    elif selected_page == "Users":
        render_admin_users()

    elif selected_page == "Services":
        render_admin_services()

    elif selected_page == "Bookings":
        render_admin_bookings()

    elif selected_page == "Reviews":
        render_admin_reviews()

    elif selected_page == "Reports":
        render_admin_reports()

    else:
        st.error("Admin page not found.")


def render_admin_dashboard():
    page_title(
        "Admin Dashboard",
        "System-level statistics and charts will be shown here.",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Users", "-")

    with col2:
        st.metric("Total Bookings", "-")

    with col3:
        st.metric("Total Revenue", "-")

    placeholder_page(
        "Admin charts",
        "Later, this page will connect to DashboardService.",
    )


def render_admin_users():
    page_title(
        "User Management",
        "Admin can view users and manage user roles.",
    )

    placeholder_page(
        "Users table",
        "Later, this page will connect to UserService.",
    )


def render_admin_services():
    page_title(
        "Service Management",
        "Admin can view and manage all provider services.",
    )

    placeholder_page(
        "All services",
        "Later, this page will connect to ServiceService.",
    )


def render_admin_bookings():
    page_title(
        "Booking Management",
        "Admin can view all bookings and force approve or cancel bookings.",
    )

    placeholder_page(
        "All bookings",
        "Later, this page will connect to BookingService.",
    )


def render_admin_reviews():
    page_title(
        "Review Management",
        "Admin can view and manage customer reviews.",
    )

    placeholder_page(
        "All reviews",
        "Later, this page will connect to ReviewService.",
    )


def render_admin_reports():
    page_title(
        "Admin Reports",
        "Admin can generate statistical PDF reports.",
    )

    placeholder_page(
        "PDF reports",
        "Later, this page will connect to ReportService.",
    )