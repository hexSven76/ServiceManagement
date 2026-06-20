import pandas as pd
import streamlit as st
from datetime import datetime, time, timedelta

from frontend.components import page_title, placeholder_page
from frontend.provider_service_helpers import (
    create_provider_service,
    delete_provider_service,
    fetch_provider_services,
    set_provider_service_active_status,
    update_provider_service,
)
from frontend.schedule_helpers import (
    create_schedule_slot,
    delete_schedule_slot,
    fetch_schedules_for_provider_services,
    set_schedule_active_status,
)
from frontend.booking_helpers import (
    approve_provider_booking,
    cancel_provider_booking,
    fetch_provider_bookings,
    reject_provider_booking,
)
from frontend.ui_helpers import (
    format_datetime,
    format_duration_minutes,
    format_price_irr,
    show_action_error,
    status_to_table_text,
)
from frontend.service_helpers import service_is_active


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
        "Create and manage your services.",
    )

    provider_id = st.session_state.user_id

    create_service_form(provider_id)

    st.markdown("---")

    try:
        services = fetch_provider_services(provider_id)

    except Exception as error:
        show_action_error(error)
        return

    if not services:
        st.info("You have not created any services yet.")
        return

    render_provider_services_table(services)
    render_provider_service_cards(services, provider_id)


def create_service_form(provider_id: int):
    with st.expander("➕ Create New Service", expanded=True):
        with st.form("create_service_form"):
            title = st.text_input("Service Title")
            category = st.text_input("Category", placeholder="Example: Cleaning, Beauty, Repair")
            description = st.text_area("Description")

            col1, col2, col3 = st.columns(3)

            with col1:
                price = st.number_input(
                    "Price",
                    min_value=0.0,
                    step=10.0,
                )

            with col2:
                duration = st.number_input(
                    "Duration",
                    min_value=1,
                    step=5,
                    help="Duration in minutes",
                )

            with col3:
                is_active = st.checkbox("Active", value=True)

            submitted = st.form_submit_button("Create Service")

        if submitted:
            if not title.strip():
                st.warning("Service title is required.")
                return

            try:
                create_provider_service(
                    provider_id=provider_id,
                    title=title.strip(),
                    description=description.strip(),
                    category=category.strip() or "Uncategorized",
                    price=float(price),
                    duration=int(duration),
                    is_active=is_active,
                )

                st.success("Service created successfully.")
                st.rerun()

            except Exception as error:
                show_action_error(error)


def render_provider_services_table(services: list[dict]):
    st.subheader("My Services Table")

    table_data = []

    for service in services:
        table_data.append(
            {
                "ID": service.get("id"),
                "Title": service.get("title"),
                "Category": service.get("category"),
                "Price": format_price_irr(service.get("price")),
                "Duration": format_duration_minutes(service.get("duration")),
                "Status": status_to_table_text(service.get("status")),
            }
        )

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_provider_service_cards(services: list[dict], provider_id: int):
    st.subheader("Manage Services")

    for service in services:
        service_id = service.get("id")

        with st.container(border=True):
            st.markdown(f"### {service.get('title')}")
            st.caption(f"Service ID: {service_id}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Price", format_price_irr(service.get("price")))

            with col2:
                st.metric("Duration", format_duration_minutes(service.get("duration")))

            with col3:
                if service_is_active(service):
                    st.success("Active")
                else:
                    st.warning("Inactive")

            st.write(service.get("description") or "No description provided.")

            edit_service_form(service, provider_id)

            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if service_is_active(service):
                    if st.button(
                        "Deactivate",
                        key=f"deactivate_service_{service_id}",
                        use_container_width=True,
                    ):
                        try:
                            set_provider_service_active_status(
                                service_id=service_id,
                                provider_id=provider_id,
                                is_active=False,
                            )
                            st.success("Service deactivated.")
                            st.rerun()

                        except Exception as error:
                            show_action_error(error)
                else:
                    if st.button(
                        "Activate",
                        key=f"activate_service_{service_id}",
                        use_container_width=True,
                    ):
                        try:
                            set_provider_service_active_status(
                                service_id=service_id,
                                provider_id=provider_id,
                                is_active=True,
                            )
                            st.success("Service activated.")
                            st.rerun()

                        except Exception as error:
                            show_action_error(error)

            with action_col2:
                confirm_delete = st.checkbox(
                    "Confirm delete",
                    key=f"confirm_delete_service_{service_id}",
                )

                if st.button(
                    "Delete",
                    key=f"delete_service_{service_id}",
                    use_container_width=True,
                    disabled=not confirm_delete,
                ):
                    try:
                        delete_provider_service(
                            service_id=service_id,
                            provider_id=provider_id,
                        )
                        st.success("Service deleted.")
                        st.rerun()

                    except Exception as error:
                        show_action_error(error)


def edit_service_form(service: dict, provider_id: int):
    service_id = service.get("id")

    with st.expander("Edit Service"):
        with st.form(f"edit_service_form_{service_id}"):
            title = st.text_input(
                "Service Title",
                value=service.get("title") or "",
                key=f"edit_title_{service_id}",
            )

            category = st.text_input(
                "Category",
                value=service.get("category") or "Uncategorized",
                key=f"edit_category_{service_id}",
            )

            description = st.text_area(
                "Description",
                value=service.get("description") or "",
                key=f"edit_description_{service_id}",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                price = st.number_input(
                    "Price",
                    min_value=0.0,
                    step=10.0,
                    value=float(service.get("price") or 0),
                    key=f"edit_price_{service_id}",
                )

            with col2:
                duration = st.number_input(
                    "Duration",
                    min_value=1,
                    step=5,
                    value=int(service.get("duration") or 1),
                    key=f"edit_duration_{service_id}",
                )

            with col3:
                is_active = st.checkbox(
                    "Active",
                    value=service_is_active(service),
                    key=f"edit_active_{service_id}",
                )

            submitted = st.form_submit_button("Save Changes")

        if submitted:
            if not title.strip():
                st.warning("Service title is required.")
                return

            try:
                update_provider_service(
                    service_id=service_id,
                    provider_id=provider_id,
                    title=title.strip(),
                    description=description.strip(),
                    category=category.strip() or "Uncategorized",
                    price=float(price),
                    duration=int(duration),
                    is_active=is_active,
                )

                st.success("Service updated successfully.")
                st.rerun()

            except Exception as error:
                show_action_error(error)


def render_provider_schedule():
    page_title(
        "Schedule Management",
        "Define available time slots for your services.",
    )

    provider_id = st.session_state.user_id

    try:
        services = fetch_provider_services(provider_id)

    except Exception as error:
        show_action_error(error)
        return

    if not services:
        st.info("You need to create at least one service before defining schedule slots.")
        return

    service_options = {
        f"{service.get('title')} | ID: {service.get('id')}": service
        for service in services
    }

    selected_service_label = st.selectbox(
        "Select Service",
        list(service_options.keys()),
    )

    selected_service = service_options[selected_service_label]
    selected_service_id = selected_service.get("id")

    create_schedule_form(
        provider_id=provider_id,
        selected_service=selected_service,
    )
    st.markdown("---")

    provider_service_ids = [service.get("id") for service in services]

    try:
        schedules = fetch_schedules_for_provider_services(provider_service_ids)

    except Exception as error:
        show_action_error(error)
        return

    selected_service_schedules = [
        slot for slot in schedules
        if slot.get("service_id") == selected_service_id
    ]

    if not selected_service_schedules:
        st.info("No schedule slots have been created for this service yet.")
        return

    render_schedule_table(selected_service_schedules)
    render_schedule_cards(
        schedules=selected_service_schedules,
        provider_service_ids=provider_service_ids,
    )


def create_schedule_form(provider_id: int, selected_service: dict):
    selected_service_id = selected_service.get("id")

    raw_duration = (
        selected_service.get("duration_minutes")
        or selected_service.get("duration")
        or 0
    )

    try:
        duration_minutes = int(raw_duration)
    except (TypeError, ValueError):
        duration_minutes = 0

    with st.expander("➕ Create New Time Slot", expanded=True):
        st.write(f"**Selected service:** {selected_service.get('title')}")
        st.write(f"**Service duration:** {duration_minutes} minutes")

        if not selected_service_id:
            st.error("Selected service is invalid.")
            return

        if duration_minutes <= 0:
            st.error("This service has no valid duration. Edit the service duration first.")
            return

        with st.form("create_schedule_form"):
            slot_date = st.date_input("Date")

            col1, col2, col3 = st.columns(3)

            with col1:
                start_time_value = st.time_input(
                    "Start Time",
                    value=time(9, 0),
                )

            start_datetime_preview = datetime.combine(slot_date, start_time_value)
            end_datetime_preview = start_datetime_preview + timedelta(
                minutes=duration_minutes
            )

            with col2:
                st.text_input(
                    "End Time",
                    value=end_datetime_preview.strftime("%H:%M"),
                    disabled=True,
                    help="End time is calculated automatically from service duration.",
                )

            with col3:
                is_active = st.checkbox("Active", value=True)

            st.caption(
                "The end time is calculated automatically because the backend requires "
                "slot duration to exactly match service duration."
            )

            submitted = st.form_submit_button("Create Time Slot")

            if submitted:
                start_datetime = datetime.combine(slot_date, start_time_value)
                end_datetime = start_datetime + timedelta(minutes=duration_minutes)

                try:
                    create_schedule_slot(
                        service_id=selected_service_id,
                        provider_id=provider_id,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        is_active=is_active,
                    )
                    st.success("Schedule slot created successfully.")
                    st.rerun()

                except Exception as error:
                    show_action_error(error)


def render_schedule_table(schedules: list[dict]):
    st.subheader("Schedule Slots Table")

    table_data = []

    for slot in schedules:
        start_datetime = slot.get("start_datetime")
        end_datetime = slot.get("end_datetime")

        table_data.append(
            {
                "ID": slot.get("id"),
                "Date": start_datetime.date() if start_datetime else "-",
                "Start": start_datetime.strftime("%H:%M") if start_datetime else "-",
                "End": end_datetime.strftime("%H:%M") if end_datetime else "-",
                "Active": "Yes" if slot.get("is_active") else "No",
                "Booked": "Yes" if slot.get("is_booked") else "No",
                "Status": slot.get("status") or "-",
            }
        )

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_schedule_cards(
    schedules: list[dict],
    provider_service_ids: list[int],
):
    st.subheader("Manage Schedule Slots")

    for slot in schedules:
        schedule_id = slot.get("id")
        start_datetime = slot.get("start_datetime")
        end_datetime = slot.get("end_datetime")

        with st.container(border=True):
            st.markdown(f"### Slot #{schedule_id}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Start:** {format_datetime(start_datetime)}")

            with col2:
                st.write(f"**End:** {format_datetime(end_datetime)}")

            with col3:
                st.write(f"**Status:** {status_to_table_text(slot.get('status'))}")
            status_col1, status_col2, status_col3 = st.columns(3)

            with status_col1:
                if slot.get("is_active"):
                    st.success("Active")
                else:
                    st.warning("Inactive")

            with status_col2:
                if slot.get("is_booked"):
                    st.error("Booked")
                else:
                    st.info("Available")

            with status_col3:
                st.caption(f"Status: {status_to_table_text(slot.get('status'))}")

            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if slot.get("is_active"):
                    if st.button(
                        "Deactivate",
                        key=f"deactivate_schedule_{schedule_id}",
                        use_container_width=True,
                    ):
                        try:
                            set_schedule_active_status(
                                schedule_id=schedule_id,
                                provider_service_ids=provider_service_ids,
                                is_active=False,
                            )

                            st.success("Schedule slot deactivated.")
                            st.rerun()

                        except Exception as error:
                            show_action_error(error)
                else:
                    if st.button(
                        "Activate",
                        key=f"activate_schedule_{schedule_id}",
                        use_container_width=True,
                    ):
                        try:
                            set_schedule_active_status(
                                schedule_id=schedule_id,
                                provider_service_ids=provider_service_ids,
                                is_active=True,
                            )

                            st.success("Schedule slot activated.")
                            st.rerun()

                        except Exception as error:
                            show_action_error(error)

            with action_col2:
                confirm_delete = st.checkbox(
                    "Confirm delete",
                    key=f"confirm_delete_schedule_{schedule_id}",
                )

                if st.button(
                    "Delete",
                    key=f"delete_schedule_{schedule_id}",
                    use_container_width=True,
                    disabled=not confirm_delete,
                ):
                    if slot.get("is_booked"):
                        st.warning("Booked slots should not be deleted.")
                    else:
                        try:
                            delete_schedule_slot(
                                schedule_id=schedule_id,
                                provider_service_ids=provider_service_ids,
                            )

                            st.success("Schedule slot deleted.")
                            st.rerun()

                        except Exception as error:
                            show_action_error(error)

def render_provider_bookings():
    page_title(
        "Provider Bookings",
        "View and manage bookings received for your services.",
    )

    success_message = st.session_state.pop("provider_booking_message", None)

    if success_message:
        st.success(success_message)

    provider_id = st.session_state.user_id

    try:
        bookings = fetch_provider_bookings(provider_id)

    except Exception as error:
        show_action_error(error)
        return

    if not bookings:
        st.info("You have not received any bookings yet.")
        return

    render_provider_bookings_table(bookings)
    render_provider_booking_cards(bookings)


def get_booking_status_upper(booking: dict) -> str:
    return str(booking.get("status") or "").upper()


def can_provider_approve_booking(booking: dict) -> bool:
    return get_booking_status_upper(booking) == "PENDING"


def can_provider_reject_booking(booking: dict) -> bool:
    return get_booking_status_upper(booking) == "PENDING"


def can_provider_cancel_booking(booking: dict) -> bool:
    return get_booking_status_upper(booking) in [
        "PENDING",
        "CONFIRMED",
        "APPROVED",
    ]


def render_provider_bookings_table(bookings: list[dict]):
    st.subheader("Received Bookings Table")

    table_data = []

    for booking in bookings:
        table_data.append(
            {
                "Booking ID": booking.get("id"),
                "Customer": booking.get("customer_name"),
                "Service": booking.get("service_title"),
                "Start": format_datetime(booking.get("slot_start")),
                "End": format_datetime(booking.get("slot_end")),
                "Status": status_to_table_text(booking.get("status")),
                "Payment": status_to_table_text(booking.get("payment_status")),
                "Slot ID": booking.get("schedule_id") or "-",
            }
        )

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )
    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_provider_booking_cards(bookings: list[dict]):
    st.subheader("Manage Received Bookings")

    for booking in bookings:
        booking_id = booking.get("id")
        slot_start = booking.get("slot_start")
        slot_end = booking.get("slot_end")

        with st.container(border=True):
            st.markdown(f"### Booking #{booking_id}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Customer:** {booking.get('customer_name')}")
                st.write(f"**Customer Email:** {booking.get('customer_email')}")
                st.write(f"**Service:** {booking.get('service_title')}")

            with col2:
                st.write(f"**Start:** {format_datetime(slot_start)}")
                st.write(f"**End:** {format_datetime(slot_end)}")

            with col3:
                st.write(f"**Status:** {status_to_table_text(booking.get('status'))}")
                st.write(f"**Payment:** {status_to_table_text(booking.get('payment_status'))}")
                st.write(f"**Slot ID:** {booking.get('schedule_id') or '-'}")

            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                if st.button(
                    "Approve",
                    key=f"approve_booking_{booking_id}",
                    use_container_width=True,
                    disabled=not can_provider_approve_booking(booking),
                ):
                    try:
                        approve_provider_booking(
                            booking_id=booking_id,
                            provider_id=st.session_state.user_id,
                        )

                        st.session_state.provider_booking_message = (
                            f"Booking #{booking_id} approved successfully."
                        )

                        st.rerun()

                    except Exception as error:
                        show_action_error(error)

            with action_col2:
                confirm_reject = st.checkbox(
                    "Confirm reject",
                    key=f"confirm_reject_booking_{booking_id}",
                    disabled=not can_provider_reject_booking(booking),
                )

                if st.button(
                    "Reject",
                    key=f"reject_booking_{booking_id}",
                    use_container_width=True,
                    disabled=(
                        not can_provider_reject_booking(booking)
                        or not confirm_reject
                    ),
                ):
                    try:
                        reject_provider_booking(
                            booking_id=booking_id,
                            provider_id=st.session_state.user_id,
                        )

                        st.session_state.provider_booking_message = (
                            f"Booking #{booking_id} rejected successfully."
                        )

                        st.rerun()

                    except Exception as error:
                        show_action_error(error)

            with action_col3:
                confirm_cancel = st.checkbox(
                    "Confirm cancel",
                    key=f"confirm_cancel_provider_booking_{booking_id}",
                    disabled=not can_provider_cancel_booking(booking),
                )

                if st.button(
                    "Cancel",
                    key=f"cancel_provider_booking_{booking_id}",
                    use_container_width=True,
                    disabled=(
                        not can_provider_cancel_booking(booking)
                        or not confirm_cancel
                    ),
                ):
                    try:
                        cancel_provider_booking(
                            booking_id=booking_id,
                            provider_id=st.session_state.user_id,
                        )

                        st.session_state.provider_booking_message = (
                            f"Booking #{booking_id} canceled successfully."
                        )

                        st.rerun()

                    except Exception as error:
                        show_action_error(error)


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