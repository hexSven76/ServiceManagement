from pathlib import Path

import pandas as pd
import streamlit as st

from app.exceptions import AppError
from frontend.components import page_title, placeholder_page
from frontend.service_helpers import (
    fetch_all_services,
    filter_services,
    find_service_by_id,
)
from frontend.session import clear_selected_service, select_service
from frontend.schedule_helpers import fetch_available_schedules_for_service
from frontend.booking_helpers import create_customer_booking


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
    try:
        services = fetch_all_services()

    except AppError as error:
        st.error(str(error))
        return

    except Exception as error:
        st.error("Unexpected error while loading services.")
        st.exception(error)
        return

    if st.session_state.selected_service_id is not None:
        selected_service = find_service_by_id(
            services=services,
            service_id=st.session_state.selected_service_id,
        )

        if selected_service is None:
            st.error("Selected service was not found.")
            if st.button("Back to Browse"):
                clear_selected_service()
                st.rerun()
            return

        render_service_detail(selected_service)
        return

    page_title(
        "Browse Services",
        "Search and filter available services.",
    )

    if not services:
        st.info("No services have been created yet.")
        return

    render_service_filters_and_results(services)


def render_service_filters_and_results(services: list[dict]):
    st.subheader("Filters")

    categories = sorted(
        {
            service.get("category")
            for service in services
            if service.get("category")
        }
    )

    providers = sorted(
        {
            service.get("provider_name")
            for service in services
            if service.get("provider_name")
        }
    )

    prices = [service.get("price") or 0 for service in services]
    min_available_price = int(min(prices)) if prices else 0
    max_available_price = int(max(prices)) if prices else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        search_text = st.text_input(
            "Search",
            placeholder="Search by service, category, provider...",
        )

    with col2:
        selected_category = st.selectbox(
            "Category",
            ["All"] + categories,
        )

    with col3:
        selected_provider = st.selectbox(
            "Provider",
            ["All"] + providers,
        )

    col4, col5 = st.columns([2, 1])

    with col4:
        if min_available_price == max_available_price:
            selected_price_range = (
                min_available_price,
                max_available_price,
            )
            st.caption(f"Price: {min_available_price}")
        else:
            selected_price_range = st.slider(
                "Price range",
                min_value=min_available_price,
                max_value=max_available_price,
                value=(min_available_price, max_available_price),
            )

    with col5:
        active_only = st.checkbox(
            "Active services only",
            value=True,
        )

    filtered_services = filter_services(
        services=services,
        search_text=search_text,
        category=selected_category,
        provider=selected_provider,
        min_price=selected_price_range[0],
        max_price=selected_price_range[1],
        active_only=active_only,
    )

    st.markdown("---")

    st.write(f"Found **{len(filtered_services)}** service(s).")

    if not filtered_services:
        st.warning("No services match your filters.")
        return

    render_services_table(filtered_services)
    render_service_cards(filtered_services)


def render_services_table(services: list[dict]):
    table_data = []

    for service in services:
        table_data.append(
            {
                "ID": service.get("id"),
                "Title": service.get("title"),
                "Category": service.get("category"),
                "Provider": service.get("provider_name"),
                "Price": service.get("price"),
                "Duration": service.get("duration"),
                "Active": "Yes" if service.get("is_active") else "No",
            }
        )

    df = pd.DataFrame(table_data)

    st.subheader("Services Table")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_service_cards(services: list[dict]):
    st.subheader("Service Cards")

    for service in services:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {service.get('title')}")
                st.caption(
                    f"Category: {service.get('category')} | "
                    f"Provider: {service.get('provider_name')}"
                )

                description = service.get("description") or "No description provided."
                st.write(description)

            with col2:
                st.metric("Price", service.get("price"))
                st.metric("Duration", service.get("duration"))

                if service.get("is_active"):
                    st.success("Active")
                else:
                    st.warning("Inactive")

            if st.button(
                "View Details",
                key=f"view_service_{service.get('id')}",
                use_container_width=True,
            ):
                select_service(service.get("id"))
                st.rerun()


def render_service_detail(service: dict):
    if st.button("← Back to Browse"):
        clear_selected_service()
        st.rerun()

    st.markdown("---")

    page_title(
        service.get("title", "Service Details"),
        "Full service information.",
    )

    image_path = service.get("image_path")
    safe_image_path = Path(image_path) if image_path else None

    if safe_image_path and safe_image_path.exists():
        st.image(str(safe_image_path), use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Price", service.get("price"))

    with col2:
        st.metric("Duration", service.get("duration"))

    with col3:
        if service.get("is_active"):
            st.success("Active")
        else:
            st.warning("Inactive")

    st.markdown("### Description")
    st.write(service.get("description") or "No description provided.")

    st.markdown("### Service Information")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.write(f"**Service ID:** {service.get('id')}")
        st.write(f"**Category:** {service.get('category')}")
        st.write(f"**Provider:** {service.get('provider_name')}")

    with info_col2:
        st.write(f"**Provider ID:** {service.get('provider_id')}")
        st.write(f"**Status:** {'Active' if service.get('is_active') else 'Inactive'}")
        st.write(f"**Image:** {service.get('image_path') or 'No image'}")

    st.markdown("---")

    render_available_slots_for_service(service)

def render_available_slots_for_service(service: dict):
    st.subheader("Available Time Slots")

    success_message = st.session_state.pop("booking_success_message", None)

    if success_message:
        st.success(success_message)

    service_id = service.get("id")

    try:
        available_slots = fetch_available_schedules_for_service(service_id)

    except Exception as error:
        st.error("Could not load available time slots.")
        st.exception(error)
        return

    if not available_slots:
        st.info("No available time slots for this service yet.")
        return

    render_available_slots_table(available_slots)
    selected_slot_id = render_available_slots_selector(available_slots)

    selected_slot = next(
        (
            slot
            for slot in available_slots
            if slot.get("id") == selected_slot_id
        ),
        None,
    )

    if selected_slot is None:
        st.warning("Please select a valid time slot.")
        return

    render_booking_summary(
        service=service,
        slot=selected_slot,
    )

    if st.button(
        "Book Selected Slot",
        use_container_width=True,
        type="primary",
    ):
        try:
            booking = create_customer_booking(
                customer_id=st.session_state.user_id,
                service=service,
                slot_id=selected_slot_id,
            )

            st.session_state.booking_success_message = (
                f"Booking #{booking.get('id')} created successfully. "
                f"Status: {booking.get('status') or 'PENDING'}."
            )

            st.rerun()

        except Exception as error:
            st.error("Could not create booking.")
            st.exception(error)

def render_available_slots_table(slots: list[dict]):
    table_data = []

    for slot in slots:
        start_datetime = slot.get("start_datetime")
        end_datetime = slot.get("end_datetime")

        table_data.append(
            {
                "Slot ID": slot.get("id"),
                "Date": start_datetime.date() if start_datetime else "-",
                "Start": start_datetime.strftime("%H:%M") if start_datetime else "-",
                "End": end_datetime.strftime("%H:%M") if end_datetime else "-",
                "Status": slot.get("status") or "-",
            }
        )

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

def render_booking_summary(service: dict, slot: dict):
    start_datetime = slot.get("start_datetime")
    end_datetime = slot.get("end_datetime")

    st.markdown("### Booking Summary")

    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Service:** {service.get('title')}")
            st.write(f"**Provider:** {service.get('provider_name')}")
            st.write(f"**Price:** {service.get('price')}")

        with col2:
            st.write(
                f"**Date:** {start_datetime.date() if start_datetime else '-'}"
            )
            st.write(
                f"**Time:** "
                f"{start_datetime.strftime('%H:%M') if start_datetime else '-'}"
                f" - "
                f"{end_datetime.strftime('%H:%M') if end_datetime else '-'}"
            )
            st.write(f"**Slot ID:** {slot.get('id')}")

def render_available_slots_selector(slots: list[dict]) -> int | None:
    slot_options = {}

    for slot in slots:
        slot_id = slot.get("id")
        start_datetime = slot.get("start_datetime")
        end_datetime = slot.get("end_datetime")

        if start_datetime and end_datetime:
            label = (
                f"Slot #{slot_id} | "
                f"{start_datetime.date()} | "
                f"{start_datetime.strftime('%H:%M')} - "
                f"{end_datetime.strftime('%H:%M')}"
            )
        else:
            label = f"Slot #{slot_id}"

        slot_options[label] = slot_id

    selected_label = st.radio(
        "Select a time slot",
        list(slot_options.keys()),
    )

    return slot_options[selected_label]



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