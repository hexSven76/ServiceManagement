from pathlib import Path

import pandas as pd
import streamlit as st

from app.exceptions import AppError
from frontend.components import page_title, placeholder_page
from frontend.service_helpers import (
    fetch_all_services,
    filter_services,
    find_service_by_id,
    service_is_active,
)
from frontend.session import clear_selected_service, select_service
from frontend.schedule_helpers import fetch_available_schedules_for_service
from frontend.booking_helpers import (
    can_customer_cancel_booking,
    cancel_customer_booking,
    create_customer_booking,
    fetch_customer_bookings,
)
from frontend.ui_helpers import (
    format_datetime,
    format_duration_minutes,
    format_price_irr,
    show_action_error,
    status_to_table_text,
)
from frontend.customer_review_helpers import (
    enrich_services_with_review_summary,
    fetch_service_review_summary,
    format_rating,
)




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
        show_action_error(error)
        return

    try:
        services = enrich_services_with_review_summary(services)

    except Exception as error:
        show_action_error(error)
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
            st.caption(f"Price: {format_price_irr(min_available_price)}")
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
                "Price": format_price_irr(service.get("price")),
                "Duration": format_duration_minutes(service.get("duration")),
                "Status": status_to_table_text(service.get("status")),
                "Rating": format_rating(
                    service.get("average_rating"),
                    service.get("review_count"),
                ),
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
                    f"Category: {service.get('category') or 'Uncategorized'} | "
                    f"Provider: {service.get('provider_name')}"
                )

                description = service.get("description") or "No description provided."
                st.write(description)

                st.write(
                    "**Rating:** "
                    f"{format_rating(service.get('average_rating'), service.get('review_count'))}"
                )

            with col2:
                st.metric("Price", format_price_irr(service.get("price")))
                st.metric(
                    "Duration",
                    format_duration_minutes(service.get("duration")),
                )

                if service_is_active(service):
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


def render_service_image(service: dict):
    image_path = service.get("image_path")
    safe_image_path = Path(image_path) if image_path else None

    if safe_image_path and safe_image_path.exists():
        st.image(str(safe_image_path), use_container_width=True)
        return

    st.info("No service image uploaded. Showing default service placeholder.")
    st.markdown(
        """
        <div style="
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 32px;
            text-align: center;
            background-color: #fafafa;
            margin-bottom: 16px;
        ">
            <div style="font-size: 48px;">🛠️</div>
            <div style="font-size: 18px; font-weight: 600;">Service Image</div>
            <div style="font-size: 14px; color: #666;">Default placeholder</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_service_detail(service: dict):
    if st.button("← Back to Browse"):
        clear_selected_service()
        st.rerun()

    st.markdown("---")

    page_title(
        service.get("title", "Service Details"),
        "Full service information.",
    )

    render_service_image(service)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Price", format_price_irr(service.get("price")))

    with col2:
        st.metric("Duration", format_duration_minutes(service.get("duration")))

    with col3:
        st.metric(
            "Rating",
            format_rating(
                service.get("average_rating"),
                service.get("review_count"),
            ),
        )

    with col4:
        if service_is_active(service):
            st.success("Active")
        else:
            st.warning("Inactive")

    st.markdown("### Description")
    st.write(service.get("description") or "No description provided.")

    st.markdown("### Service Information")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.write(f"**Service ID:** {service.get('id')}")
        st.write(f"**Category:** {service.get('category') or 'Uncategorized'}")
        st.write(f"**Provider:** {service.get('provider_name')}")

    with info_col2:
        st.write(f"**Provider ID:** {service.get('provider_id')}")
        st.write(f"**Status:** {status_to_table_text(service.get('status'))}")
        st.write(f"**Image:** {service.get('image_path') or 'Default placeholder'}")

    render_service_reviews(service)

    st.markdown("---")

    render_available_slots_for_service(service)


def render_service_reviews(service: dict):
    st.markdown("### Recent Reviews")

    service_id = service.get("id")

    if not service_id:
        st.info("Reviews are not available for this service.")
        return

    try:
        summary = fetch_service_review_summary(service_id)

    except Exception as error:
        show_action_error(error)
        return

    average_rating = summary.get("average_rating", 0.0)
    review_count = summary.get("review_count", 0)
    recent_reviews = summary.get("recent_reviews", [])

    st.write(f"**Average rating:** {format_rating(average_rating, review_count)}")

    if not recent_reviews:
        st.info("No reviews have been submitted for this service yet.")
        return

    for review in recent_reviews:
        with st.container(border=True):
            st.write(
                f"**{review.get('rating')}/5** by "
                f"{review.get('customer_name')}"
            )

            if review.get("comment"):
                st.write(review.get("comment"))
            else:
                st.caption("No comment provided.")

            st.caption(review.get("created_at_text") or "-")


def render_available_slots_for_service(service: dict):
    st.subheader("Available Time Slots")

    success_message = st.session_state.pop("booking_success_message", None)

    if success_message:
        st.success(success_message)

    service_id = service.get("id")

    try:
        available_slots = fetch_available_schedules_for_service(service_id)

    except Exception as error:
        show_action_error(error)
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
            show_action_error(error)


def render_available_slots_table(slots: list[dict]):
    table_data = []

    for slot in slots:
        table_data.append(
            {
                "Slot ID": slot.get("id"),
                "Start": format_datetime(slot.get("start_datetime")),
                "End": format_datetime(slot.get("end_datetime")),
                "Status": status_to_table_text(slot.get("status")),
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
            st.write(f"**Price:** {format_price_irr(service.get('price'))}")

        with col2:
            st.write(f"**Start:** {format_datetime(start_datetime)}")
            st.write(f"**End:** {format_datetime(end_datetime)}")
            st.write(f"**Slot ID:** {slot.get('id')}")


def render_available_slots_selector(slots: list[dict]) -> int | None:
    slot_options = {}

    for slot in slots:
        slot_id = slot.get("id")
        start_datetime = slot.get("start_datetime")
        end_datetime = slot.get("end_datetime")

        label = (
            f"Slot #{slot_id} | "
            f"{format_datetime(start_datetime)} - "
            f"{format_datetime(end_datetime)}"
        )

        slot_options[label] = slot_id

    selected_label = st.radio(
        "Select a time slot",
        list(slot_options.keys()),
    )

    return slot_options[selected_label]


def render_customer_bookings():
    page_title(
        "My Bookings",
        "View and manage your service bookings.",
    )

    success_message = st.session_state.pop("customer_booking_message", None)

    if success_message:
        st.success(success_message)

    customer_id = st.session_state.user_id

    try:
        bookings = fetch_customer_bookings(customer_id)

    except Exception as error:
        show_action_error(error)
        return

    if not bookings:
        st.info("You have not created any bookings yet.")
        return

    render_customer_bookings_table(bookings)
    render_customer_booking_cards(bookings)


def render_customer_bookings_table(bookings: list[dict]):
    st.subheader("Bookings Table")

    table_data = []

    for booking in bookings:
        table_data.append(
            {
                "Booking ID": booking.get("id"),
                "Service": booking.get("service_title"),
                "Provider": booking.get("provider_name"),
                "Start": format_datetime(booking.get("slot_start")),
                "End": format_datetime(booking.get("slot_end")),
                "Status": status_to_table_text(booking.get("status")),
                "Payment": status_to_table_text(booking.get("payment_status")),
                "Cancel Deadline": format_datetime(
                    booking.get("cancel_deadline")
                ),
            }
        )

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_customer_booking_cards(bookings: list[dict]):
    st.subheader("Booking Details")

    for booking in bookings:
        booking_id = booking.get("id")
        slot_start = booking.get("slot_start")
        slot_end = booking.get("slot_end")
        cancel_deadline = booking.get("cancel_deadline")

        with st.container(border=True):
            st.markdown(f"### Booking #{booking_id}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Service:** {booking.get('service_title')}")
                st.write(f"**Provider:** {booking.get('provider_name')}")
                st.write(f"**Price:** {format_price_irr(booking.get('service_price'))}")

            with col2:
                st.write(f"**Start:** {format_datetime(slot_start)}")
                st.write(f"**End:** {format_datetime(slot_end)}")
                st.write(
                    f"**Cancel Deadline:** {format_datetime(cancel_deadline)}"
                )

            with col3:
                st.write(
                    f"**Status:** {status_to_table_text(booking.get('status'))}"
                )
                st.write(
                    f"**Payment:** {status_to_table_text(booking.get('payment_status'))}"
                )
                st.write(f"**Slot ID:** {booking.get('schedule_id') or '-'}")
                
            can_cancel, reason = can_customer_cancel_booking(booking)

            if can_cancel:
                confirm_cancel = st.checkbox(
                    "Confirm cancellation",
                    key=f"confirm_cancel_booking_{booking_id}",
                )

                if st.button(
                    "Cancel Booking",
                    key=f"cancel_booking_{booking_id}",
                    use_container_width=True,
                    disabled=not confirm_cancel,
                ):
                    try:
                        cancel_customer_booking(
                            booking_id=booking_id,
                            customer_id=st.session_state.user_id,
                        )

                        st.session_state.customer_booking_message = (
                            f"Booking #{booking_id} canceled successfully."
                        )

                        st.rerun()

                    except Exception as error:
                        show_action_error(error)

            else:
                st.info(reason)


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