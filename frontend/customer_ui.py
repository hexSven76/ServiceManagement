from datetime import datetime, timezone
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
from frontend.payment_helpers import (
    fetch_booking_payment,
    generate_customer_receipt_pdf,
    pay_customer_booking,
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


def get_session_role_text() -> str:
    role = st.session_state.get("role")

    if role is None:
        return ""

    if hasattr(role, "value"):
        return str(role.value).upper()

    return str(role).split(".")[-1].upper()


def is_current_user_customer() -> bool:
    return get_session_role_text() == "CUSTOMER"


def render_available_slots_for_service(service: dict):
    st.subheader("Available Time Slots")

    success_message = st.session_state.pop("booking_success_message", None)

    if success_message:
        st.success(success_message)

    if not is_current_user_customer():
        st.warning("Only customers can book service slots.")
        return

    if not service_is_active(service):
        st.warning("This service is currently inactive and cannot be booked.")
        return

    service_id = service.get("id")

    if not service_id:
        st.error("Service ID is missing. Booking is not available.")
        return

    try:
        available_slots = fetch_available_schedules_for_service(service_id)

    except Exception as error:
        show_action_error(error)
        return

    available_slots = sorted(
        available_slots,
        key=lambda slot: slot.get("start_datetime") or "",
    )

    if not available_slots:
        st.info("No available time slots for this service yet.")
        return

    st.caption(
        "Select one available slot below. The booking will be created as PENDING "
        "until the provider approves or rejects it."
    )

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

    confirm_booking = st.checkbox(
        "I confirm that I want to book this selected service and time slot.",
        key=f"confirm_booking_service_{service_id}_slot_{selected_slot_id}",
    )

    if st.button(
        "Book Selected Slot",
        use_container_width=True,
        type="primary",
        disabled=not confirm_booking,
    ):
        try:
            booking = create_customer_booking(
                customer_id=st.session_state.user_id,
                service=service,
                slot_id=selected_slot_id,
            )

            st.session_state.booking_success_message = (
                f"Booking #{booking.get('id')} created successfully. "
                f"Status: {status_to_table_text(booking.get('status') or 'PENDING')}. "
                f"Cancel deadline: {format_datetime(booking.get('cancel_deadline'))}."
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


def get_booking_status_upper(booking: dict) -> str:
    return str(booking.get("status") or "").upper()


def get_payment_status_upper(booking: dict) -> str:
    return str(booking.get("payment_status") or "").upper()


def get_unique_booking_values(bookings: list[dict], key: str) -> list[str]:
    values = {
        status_to_table_text(booking.get(key))
        for booking in bookings
        if booking.get(key)
    }

    return sorted(values)


def normalize_datetime_to_utc_naive(value):
    """
    Normalize DB/string datetime values so countdown comparisons are stable.

    Backend datetimes are usually naive UTC.
    Streamlit/UI may sometimes receive strings.
    """
    if value is None:
        return None

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)

    return value


def get_utc_now_naive() -> datetime:
    return datetime.utcnow()


def get_cancel_remaining_minutes(cancel_deadline) -> int | None:
    deadline = normalize_datetime_to_utc_naive(cancel_deadline)

    if deadline is None:
        return None

    remaining = deadline - get_utc_now_naive()
    return int(remaining.total_seconds() // 60)


def get_cancel_remaining_text(cancel_deadline) -> str:
    remaining_minutes = get_cancel_remaining_minutes(cancel_deadline)

    if remaining_minutes is None:
        return "No cancellation deadline"

    if remaining_minutes <= 0:
        return "Cancellation deadline passed"

    days = remaining_minutes // (24 * 60)
    hours = (remaining_minutes % (24 * 60)) // 60
    minutes = remaining_minutes % 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m remaining"

    if hours > 0:
        return f"{hours}h {minutes}m remaining"

    return f"{minutes}m remaining"


def is_cancel_deadline_active(cancel_deadline) -> bool:
    remaining_minutes = get_cancel_remaining_minutes(cancel_deadline)

    if remaining_minutes is None:
        return False

    return remaining_minutes > 0


def get_cancel_countdown_status(cancel_deadline) -> str:
    remaining_minutes = get_cancel_remaining_minutes(cancel_deadline)

    if remaining_minutes is None:
        return "missing"

    if remaining_minutes <= 0:
        return "expired"

    if remaining_minutes <= 30:
        return "urgent"

    if remaining_minutes <= 60:
        return "warning"

    return "safe"


def render_cancel_countdown(booking: dict):
    cancel_deadline = booking.get("cancel_deadline")

    deadline_text = format_datetime(cancel_deadline)
    remaining_text = get_cancel_remaining_text(cancel_deadline)
    countdown_status = get_cancel_countdown_status(cancel_deadline)

    st.write(f"**Cancel Deadline:** {deadline_text}")

    if countdown_status == "safe":
        st.success(f"Cancellation available: {remaining_text}")

    elif countdown_status == "warning":
        st.warning(f"Cancellation window is getting close: {remaining_text}")

    elif countdown_status == "urgent":
        st.error(f"Cancellation window almost expired: {remaining_text}")

    elif countdown_status == "expired":
        st.error("Cancellation deadline has passed.")

    else:
        st.info("Cancellation deadline is not available.")


def can_customer_pay_booking(booking: dict) -> bool:
    status = get_booking_status_upper(booking)
    payment_status = get_payment_status_upper(booking)

    return (
        payment_status != "PAID"
        and status not in {"CANCELED", "CANCELLED", "REJECTED"}
    )


def can_customer_download_receipt(booking: dict) -> bool:
    return get_payment_status_upper(booking) == "PAID"


def can_customer_review_booking(booking: dict) -> bool:
    status = get_booking_status_upper(booking)

    return status in {"CONFIRMED", "APPROVED", "COMPLETED"}


def filter_customer_bookings(
    bookings: list[dict],
    selected_status: str,
    selected_payment: str,
    search_text: str,
    sort_order: str,
) -> list[dict]:
    search_text = search_text.strip().lower()

    filtered = []

    for booking in bookings:
        booking_status = status_to_table_text(booking.get("status"))
        payment_status = status_to_table_text(booking.get("payment_status"))

        if selected_status != "All" and booking_status != selected_status:
            continue

        if selected_payment != "All" and payment_status != selected_payment:
            continue

        if search_text:
            searchable_text = " ".join(
                [
                    str(booking.get("service_title") or ""),
                    str(booking.get("provider_name") or ""),
                    str(booking.get("status") or ""),
                    str(booking.get("payment_status") or ""),
                ]
            ).lower()

            if search_text not in searchable_text:
                continue

        filtered.append(booking)

    if sort_order == "Newest first":
        filtered.sort(
            key=lambda booking: booking.get("created_at") or datetime.min,
            reverse=True,
        )

    elif sort_order == "Oldest first":
        filtered.sort(
            key=lambda booking: booking.get("created_at") or datetime.min,
        )

    elif sort_order == "Upcoming slot first":
        filtered.sort(
            key=lambda booking: booking.get("slot_start") or datetime.max,
        )

    return filtered


def render_customer_booking_metrics(bookings: list[dict]):
    total_bookings = len(bookings)

    active_bookings = sum(
        1
        for booking in bookings
        if get_booking_status_upper(booking)
        in {"PENDING", "CONFIRMED", "APPROVED"}
    )

    paid_bookings = sum(
        1
        for booking in bookings
        if get_payment_status_upper(booking) == "PAID"
    )

    canceled_bookings = sum(
        1
        for booking in bookings
        if get_booking_status_upper(booking) in {"CANCELED", "CANCELLED"}
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Bookings", total_bookings)

    with col2:
        st.metric("Active", active_bookings)

    with col3:
        st.metric("Paid", paid_bookings)

    with col4:
        st.metric("Canceled", canceled_bookings)


def render_customer_booking_filters(bookings: list[dict]) -> list[dict]:
    st.subheader("Filters")

    booking_statuses = get_unique_booking_values(bookings, "status")
    payment_statuses = get_unique_booking_values(bookings, "payment_status")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_status = st.selectbox(
            "Booking Status",
            ["All"] + booking_statuses,
        )

    with col2:
        selected_payment = st.selectbox(
            "Payment Status",
            ["All"] + payment_statuses,
        )

    with col3:
        sort_order = st.selectbox(
            "Sort",
            [
                "Newest first",
                "Oldest first",
                "Upcoming slot first",
            ],
        )

    search_text = st.text_input(
        "Search bookings",
        placeholder="Search by service, provider, status...",
    )

    filtered_bookings = filter_customer_bookings(
        bookings=bookings,
        selected_status=selected_status,
        selected_payment=selected_payment,
        search_text=search_text,
        sort_order=sort_order,
    )

    st.caption(
        f"Showing {len(filtered_bookings)} of {len(bookings)} booking(s)."
    )

    return filtered_bookings


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

    render_customer_booking_metrics(bookings)

    st.markdown("---")

    filtered_bookings = render_customer_booking_filters(bookings)

    if not filtered_bookings:
        st.info("No bookings match your selected filters.")
        return

    st.markdown("---")

    render_customer_bookings_table(filtered_bookings)
    render_customer_booking_cards(filtered_bookings)


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
                "Payment Action": (
                    "Paid"
                    if get_payment_status_upper(booking) == "PAID"
                    else "Available"
                    if can_customer_pay_booking(booking)
                    else "Unavailable"
                ),
                "Price": format_price_irr(booking.get("service_price")),
                "Cancel Deadline": format_datetime(
                    booking.get("cancel_deadline")
                ),
                "Cancel Time Left": get_cancel_remaining_text(
                    booking.get("cancel_deadline")
                ),
                "Cancel Status": get_cancel_countdown_status(
                    booking.get("cancel_deadline")
                ).upper(),
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
                st.write(
                    f"**Price:** "
                    f"{format_price_irr(booking.get('service_price'))}"
                )

            with col2:
                st.write(f"**Start:** {format_datetime(slot_start)}")
                st.write(f"**End:** {format_datetime(slot_end)}")
                render_cancel_countdown(booking)

            with col3:
                st.write(
                    f"**Status:** "
                    f"{status_to_table_text(booking.get('status'))}"
                )
                st.write(
                    f"**Payment:** "
                    f"{status_to_table_text(booking.get('payment_status'))}"
                )
                st.write(f"**Slot ID:** {booking.get('schedule_id') or '-'}")

            st.markdown("#### Available Actions")

            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                render_customer_cancel_action(booking)

            with action_col2:
                render_customer_payment_action_placeholder(booking)

            with action_col3:
                render_customer_review_action_placeholder(booking)


def render_customer_cancel_action(booking: dict):
    booking_id = booking.get("id")
    cancel_deadline = booking.get("cancel_deadline")

    can_cancel, reason = can_customer_cancel_booking(booking)
    deadline_active = is_cancel_deadline_active(cancel_deadline)

    if not can_cancel or not deadline_active:
        st.button(
            "Cancel Booking",
            key=f"disabled_cancel_booking_{booking_id}",
            use_container_width=True,
            disabled=True,
        )

        if not deadline_active:
            st.caption("Cancellation is disabled because the deadline has passed.")
        else:
            st.caption(reason)

        return

    confirm_cancel = st.checkbox(
        "Confirm cancellation",
        key=f"confirm_cancel_booking_{booking_id}",
    )

    st.caption(
        f"Cancellation available until "
        f"{format_datetime(cancel_deadline)} "
        f"({get_cancel_remaining_text(cancel_deadline)})."
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


def render_customer_payment_action_placeholder(booking: dict):
    booking_id = booking.get("id")
    payment_status = get_payment_status_upper(booking)

    if payment_status == "PAID":
        render_paid_booking_summary(booking)
        return

    if not can_customer_pay_booking(booking):
        st.button(
            "Pay",
            key=f"disabled_pay_booking_{booking_id}",
            use_container_width=True,
            disabled=True,
        )
        st.caption("Payment is not available for this booking state.")
        return

    with st.expander("Mock Payment", expanded=False):
        st.write(
            f"**Amount:** {format_price_irr(booking.get('service_price'))}"
        )

        payment_reference = st.text_input(
            "Payment Reference",
            placeholder="Optional reference, e.g. TEST-12345",
            key=f"payment_reference_{booking_id}",
        )

        confirm_payment = st.checkbox(
            "I confirm this mock payment.",
            key=f"confirm_payment_{booking_id}",
        )

        if st.button(
            "Pay Now",
            key=f"pay_booking_{booking_id}",
            use_container_width=True,
            type="primary",
            disabled=not confirm_payment,
        ):
            try:
                payment = pay_customer_booking(
                    customer_id=st.session_state.user_id,
                    booking_id=booking_id,
                    payment_reference=payment_reference.strip() or None,
                )

                st.session_state.customer_booking_message = (
                    f"Booking #{booking_id} paid successfully. "
                    f"Amount: {format_price_irr(payment.get('amount'))}. "
                    f"Paid at: {format_datetime(payment.get('paid_at'))}."
                )

                st.rerun()

            except Exception as error:
                show_action_error(error)


def render_paid_booking_summary(booking: dict):
    booking_id = booking.get("id")

    try:
        payment = fetch_booking_payment(booking_id)

    except Exception as error:
        show_action_error(error)
        return

    st.button(
        "Paid",
        key=f"paid_booking_{booking_id}",
        use_container_width=True,
        disabled=True,
    )

    if payment is None:
        st.caption("Payment is marked as PAID, but payment details were not found.")
        return

    st.caption(
        f"Paid {format_price_irr(payment.get('amount'))} "
        f"at {format_datetime(payment.get('paid_at'))}."
    )

    if payment.get("payment_reference"):
        st.caption(f"Reference: {payment.get('payment_reference')}")


def render_customer_review_action_placeholder(booking: dict):
    booking_id = booking.get("id")

    if can_customer_review_booking(booking):
        st.button(
            "Review",
            key=f"review_booking_placeholder_{booking_id}",
            use_container_width=True,
            disabled=True,
        )
        st.caption("Reviews will be added in CUS-NEXT-07.")
        return

    st.button(
        "Review",
        key=f"disabled_review_booking_{booking_id}",
        use_container_width=True,
        disabled=True,
    )
    st.caption("Review is not available for this booking state.")


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