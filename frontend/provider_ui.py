from pathlib import Path
from datetime import datetime, time, timedelta

import pandas as pd
import streamlit as st

from frontend.components import page_title
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
    update_schedule_slot,
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
    save_uploaded_file,
    show_action_error,
    status_to_table_text,
)
from frontend.customer_review_helpers import fetch_provider_reviews, format_rating
from frontend.profile_helpers import fetch_my_profile, update_my_profile
from frontend.provider_extra_helpers import fetch_provider_stats
from frontend.report_helpers import provider_bookings_pdf_bytes
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
        "Your services, booking statuses, and mock income summary.",
    )

    provider_id = st.session_state.user_id

    try:
        stats = fetch_provider_stats(provider_id)
    except Exception as error:
        show_action_error(error)
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("My Services", stats.get("total_services", 0))

    with col2:
        st.metric("Received Bookings", stats.get("total_bookings", 0))

    with col3:
        st.metric("Income", format_price_irr(stats.get("fake_income", 0)))

    status_counts = stats.get("booking_status_counts", {})
    if status_counts:
        st.subheader("Bookings by Status")
        st.bar_chart(pd.DataFrame({"count": status_counts}).T)
    else:
        st.info("No bookings yet.")


def render_provider_profile():
    page_title(
        "Provider Profile",
        "View and update your provider contact information.",
    )

    try:
        profile = fetch_my_profile(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    with st.form("provider_profile_form"):
        st.text_input("Username", value=profile.get("username") or "", disabled=True)
        st.text_input("Email", value=profile.get("email") or "", disabled=True)
        full_name = st.text_input("Full Name", value=profile.get("full_name") or "")
        phone = st.text_input("Phone", value=profile.get("phone") or "")
        bio = st.text_area("Bio", value=profile.get("bio") or "")
        submitted = st.form_submit_button("Save Profile")

    if submitted:
        try:
            update_my_profile(st.session_state.user_id, full_name, phone, bio)
            st.success("Profile updated successfully.")
            st.rerun()
        except Exception as error:
            show_action_error(error)


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

            uploaded_image = st.file_uploader(
                "Service Image",
                type=["jpg", "jpeg", "png", "webp"],
                key="create_service_image",
            )

            submitted = st.form_submit_button("Create Service")

        if submitted:
            if not title.strip():
                st.warning("Service title is required.")
                return

            try:
                image_path = save_uploaded_file(uploaded_image, "services") if uploaded_image else None
                create_provider_service(
                    provider_id=provider_id,
                    title=title.strip(),
                    description=description.strip(),
                    category=category.strip() or "Uncategorized",
                    price=float(price),
                    duration=int(duration),
                    is_active=is_active,
                    image_path=image_path,
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


def render_provider_service_image(service: dict):
    image_path = service.get("image_path")
    safe_image_path = Path(image_path) if image_path else None

    if safe_image_path and safe_image_path.exists():
        st.image(str(safe_image_path), use_container_width=True)
        return

    st.markdown(
        """
        <div style="
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 28px;
            text-align: center;
            background-color: #fafafa;
            margin-bottom: 16px;
        ">
            <div style="font-size: 42px;">🛠️</div>
            <div style="font-size: 18px; font-weight: 600;">Service Image</div>
            <div style="font-size: 14px; color: #666;">Default placeholder</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_provider_service_cards(services: list[dict], provider_id: int):
    st.subheader("Manage Services")

    for service in services:
        service_id = service.get("id")

        with st.container(border=True):
            st.markdown(f"### {service.get('title')}")
            st.caption(f"Service ID: {service_id}")

            render_provider_service_image(service)

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

            uploaded_image = st.file_uploader(
                "Replace Service Image",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"edit_service_image_{service_id}",
            )

            submitted = st.form_submit_button("Save Changes")

        if submitted:
            if not title.strip():
                st.warning("Service title is required.")
                return

            try:
                image_path = save_uploaded_file(uploaded_image, "services") if uploaded_image else service.get("image_path")
                update_provider_service(
                    service_id=service_id,
                    provider_id=provider_id,
                    title=title.strip(),
                    description=description.strip(),
                    category=category.strip() or "Uncategorized",
                    price=float(price),
                    duration=int(duration),
                    is_active=is_active,
                    image_path=image_path,
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
        selected_service=selected_service,
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
    selected_service: dict,
):
    st.subheader("Manage Schedule Slots")

    raw_duration = (
        selected_service.get("duration_minutes")
        or selected_service.get("duration")
        or 0
    )

    try:
        duration_minutes = int(raw_duration)
    except (TypeError, ValueError):
        duration_minutes = 0

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

            edit_schedule_slot_form(
                slot=slot,
                provider_service_ids=provider_service_ids,
                duration_minutes=duration_minutes,
            )

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


def edit_schedule_slot_form(
    slot: dict,
    provider_service_ids: list[int],
    duration_minutes: int,
):
    schedule_id = slot.get("id")
    start_datetime = slot.get("start_datetime")

    with st.expander("Edit Slot"):
        if slot.get("is_booked"):
            st.warning("Booked slots cannot be edited. Deactivate the slot if needed.")
            return

        if not start_datetime:
            st.error("This slot has no valid start time.")
            return

        if duration_minutes <= 0:
            st.error("The selected service has no valid duration. Edit the service first.")
            return

        with st.form(f"edit_schedule_form_{schedule_id}"):
            slot_date = st.date_input(
                "Date",
                value=start_datetime.date(),
                key=f"edit_schedule_date_{schedule_id}",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                start_time_value = st.time_input(
                    "Start Time",
                    value=start_datetime.time(),
                    key=f"edit_schedule_start_{schedule_id}",
                )

            new_start_datetime = datetime.combine(slot_date, start_time_value)
            new_end_datetime = new_start_datetime + timedelta(minutes=duration_minutes)

            with col2:
                st.text_input(
                    "End Time",
                    value=new_end_datetime.strftime("%H:%M"),
                    disabled=True,
                    key=f"edit_schedule_end_{schedule_id}",
                    help="End time is calculated automatically from service duration.",
                )

            with col3:
                is_active = st.checkbox(
                    "Active",
                    value=slot.get("is_active", True),
                    key=f"edit_schedule_active_{schedule_id}",
                )

            st.caption(
                "Changing the start time automatically recalculates the end time "
                "from the selected service duration."
            )

            submitted = st.form_submit_button("Save Slot Changes")

        if submitted:
            try:
                update_schedule_slot(
                    schedule_id=schedule_id,
                    provider_service_ids=provider_service_ids,
                    start_datetime=new_start_datetime,
                    end_datetime=new_end_datetime,
                    is_active=is_active,
                )

                st.success("Schedule slot updated successfully.")
                st.rerun()

            except Exception as error:
                show_action_error(error)


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
                "Customer Email": booking.get("customer_email"),
                "Service": booking.get("service_title"),
                "Start": format_datetime(booking.get("slot_start")),
                "End": format_datetime(booking.get("slot_end")),
                "Booking Status": status_to_table_text(booking.get("status")),
                "Payment Status": status_to_table_text(booking.get("payment_status")),
                "Slot ID": booking.get("schedule_id") or "-",
            }
        )

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


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

    filtered_bookings = render_provider_booking_filters(bookings)

    if not filtered_bookings:
        st.info("No bookings match the selected filters.")
        return

    render_provider_bookings_table(filtered_bookings)
    render_provider_booking_cards(filtered_bookings)


def get_provider_booking_filter_options(bookings: list[dict], field_name: str) -> list[str]:
    values = {
        status_to_table_text(booking.get(field_name))
        for booking in bookings
        if booking.get(field_name)
    }

    return sorted(values)


def render_provider_booking_filters(bookings: list[dict]) -> list[dict]:
    st.subheader("Booking Filters")

    status_options = get_provider_booking_filter_options(bookings, "status")
    payment_options = get_provider_booking_filter_options(bookings, "payment_status")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_status = st.selectbox(
            "Booking Status",
            ["All"] + status_options,
            key="provider_booking_status_filter",
        )

    with col2:
        selected_payment = st.selectbox(
            "Payment Status",
            ["All"] + payment_options,
            key="provider_booking_payment_filter",
        )

    with col3:
        search_text = st.text_input(
            "Search",
            placeholder="Customer, service, email, booking ID...",
            key="provider_booking_search_filter",
        )

    filtered = []
    search_text = search_text.strip().lower()

    for booking in bookings:
        booking_status = status_to_table_text(booking.get("status"))
        payment_status = status_to_table_text(booking.get("payment_status"))

        if selected_status != "All" and booking_status != selected_status:
            continue

        if selected_payment != "All" and payment_status != selected_payment:
            continue

        searchable_text = " ".join(
            str(value or "")
            for value in [
                booking.get("id"),
                booking.get("customer_name"),
                booking.get("customer_email"),
                booking.get("service_title"),
                booking.get("status"),
                booking.get("payment_status"),
                booking.get("schedule_id"),
            ]
        ).lower()

        if search_text and search_text not in searchable_text:
            continue

        filtered.append(booking)

    st.caption(f"Showing {len(filtered)} of {len(bookings)} received bookings.")

    return filtered


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
        "Reviews submitted for your services.",
    )

    try:
        reviews = fetch_provider_reviews(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    if not reviews:
        st.info("No reviews have been submitted for your services yet.")
        return

    avg = sum(review.get("rating", 0) for review in reviews) / len(reviews)
    st.metric("Average Rating", format_rating(avg, len(reviews)))

    table_data = [
        {
            "Review ID": review.get("id"),
            "Booking ID": review.get("booking_id"),
            "Service": review.get("service_title"),
            "Customer": review.get("customer_name"),
            "Rating": review.get("rating"),
            "Comment": review.get("comment") or "-",
            "Created": review.get("created_at_text"),
        }
        for review in reviews
    ]
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)


def render_provider_reports():
    page_title(
        "Provider Reports",
        "Generate PDF reports for your received bookings.",
    )

    pdf_state_key = f"provider_bookings_pdf_{st.session_state.user_id}"

    if st.button(
        "Prepare Provider Bookings PDF",
        key="prepare_provider_bookings_pdf",
        use_container_width=True,
    ):
        try:
            st.session_state[pdf_state_key] = provider_bookings_pdf_bytes(
                st.session_state.user_id
            )
            st.success("Provider bookings PDF is ready.")
        except Exception as error:
            show_action_error(error)

    if st.session_state.get(pdf_state_key):
        st.download_button(
            "Download Provider Bookings PDF",
            data=st.session_state[pdf_state_key],
            file_name=f"provider_{st.session_state.user_id}_bookings.pdf",
            mime="application/pdf",
            key="download_provider_bookings_pdf",
            use_container_width=True,
        )