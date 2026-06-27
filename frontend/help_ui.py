import streamlit as st

from frontend.components import page_title


def render_help_page():
    page_title("Help / About", "Demo guide for the Service Booking and Management System.")

    st.markdown(
        """
        ### Customer workflow
        1. Browse active services.
        2. Open service details and pick a free slot.
        3. Create a booking. New bookings start as **PENDING**.
        4. Pay with the mock payment form.
        5. Download the receipt PDF and submit one review after confirmation.

        ### Provider workflow
        1. Create services and upload optional images.
        2. Create slots. Slot duration is calculated from the service duration.
        3. Approve, reject, or cancel received bookings.
        4. Review dashboard metrics, customer reviews, and PDF exports.

        ### Admin workflow
        1. View KPIs and charts.
        2. Manage users, roles, service status, bookings, reviews, and reports.
        3. Export admin, provider, and customer PDFs.

        ### Demo credentials
        - Admin: `admin` / `admin123`
        - Provider: `provider` / `provider123`
        - Customer: `customer` / `customer123`

        Payment is simulated for class/demo purposes. No real payment gateway is connected.
        """
    )
