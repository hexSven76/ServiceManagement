import streamlit as st

from frontend.components import page_title, placeholder_page


def render_provider_page(selected_page: str):
    if selected_page == "Dashboard":
        render_provider_dashboard()

    elif selected_page == "Profile":
        render_provider_profile()

    elif selected_page == "My Services":
        render_provider_services()

    elif selected_page == "Schedule":
        render_provider_schedule()

    elif selected_page == "Bookings":
        render_provider_bookings()

    elif selected_page == "Reviews":
        render_provider_reviews()

    elif selected_page == "Reports":
        render_provider_reports()

    else:
        st.error("Provider page not found.")


def render_provider_dashboard():
    page_title(
        "Provider Dashboard",
        "Provider statistics and income summary will be shown here.",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("My Services", "-")

    with col2:
        st.metric("Received Bookings", "-")

    with col3:
        st.metric("Income", "-")

    placeholder_page(
        "Provider charts",
        "Later, this page will connect to DashboardService.",
    )


def render_provider_profile():
    page_title(
        "Provider Profile",
        "Provider can edit profile and contact information.",
    )

    placeholder_page(
        "Profile form",
        "Later, this page will connect to UserService.",
    )


def render_provider_services():
    page_title(
        "My Services",
        "Provider can create, edit, delete, activate, and deactivate services.",
    )

    placeholder_page(
        "Service CRUD",
        "Later, this page will connect to ServiceService.",
    )


def render_provider_schedule():
    page_title(
        "Schedule Management",
        "Provider can define available time slots for services.",
    )

    placeholder_page(
        "Time slot management",
        "Later, this page will connect to ScheduleService.",
    )


def render_provider_bookings():
    page_title(
        "Provider Bookings",
        "Provider can view, approve, reject, or cancel received bookings.",
    )

    placeholder_page(
        "Received bookings",
        "Later, this page will connect to BookingService.",
    )


def render_provider_reviews():
    page_title(
        "Provider Reviews",
        "Provider can view reviews for their services.",
    )

    placeholder_page(
        "Service reviews",
        "Later, this page will connect to ReviewService.",
    )


def render_provider_reports():
    page_title(
        "Provider Reports",
        "Provider can generate PDF reports for their bookings.",
    )

    placeholder_page(
        "Provider PDF reports",
        "Later, this page will connect to ReportService.",
    )