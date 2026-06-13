import streamlit as st

from frontend.components import page_title, placeholder_page


def render_customer_page(selected_page: str):
    if selected_page == "Browse Services":
        render_browse_services()

    elif selected_page == "My Bookings":
        render_customer_bookings()

    elif selected_page == "Profile":
        render_customer_profile()

    elif selected_page == "Reviews":
        render_customer_reviews()

    elif selected_page == "Payments":
        render_customer_payments()

    else:
        st.error("Customer page not found.")


def render_browse_services():
    page_title(
        "Browse Services",
        "Customer can search, filter, and book available services.",
    )

    placeholder_page(
        "Service search and booking",
        "Later, this page will connect to ServiceService and BookingService.",
    )


def render_customer_bookings():
    page_title(
        "My Bookings",
        "Customer can view and cancel their own bookings.",
    )

    placeholder_page(
        "Customer bookings",
        "Later, this page will connect to BookingService.",
    )


def render_customer_profile():
    page_title(
        "Customer Profile",
        "Customer can edit profile and contact information.",
    )

    placeholder_page(
        "Profile form",
        "Later, this page will connect to UserService.",
    )


def render_customer_reviews():
    page_title(
        "My Reviews",
        "Customer can submit and view service reviews.",
    )

    placeholder_page(
        "Customer reviews",
        "Later, this page will connect to ReviewService.",
    )


def render_customer_payments():
    page_title(
        "Payments",
        "Customer can pay for bookings and download payment receipts.",
    )

    placeholder_page(
        "Payment page",
        "Later, this page will connect to PaymentService and ReportService.",
    )