import pandas as pd
import streamlit as st

from frontend.components import page_title, placeholder_page
from frontend.provider_service_helpers import (
    create_provider_service,
    delete_provider_service,
    fetch_provider_services,
    set_provider_service_active_status,
    update_provider_service,
)


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
        st.error("Could not load provider services.")
        st.exception(error)
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
                st.error("Could not create service.")
                st.exception(error)


def render_provider_services_table(services: list[dict]):
    st.subheader("My Services Table")

    table_data = []

    for service in services:
        table_data.append(
            {
                "ID": service.get("id"),
                "Title": service.get("title"),
                "Category": service.get("category"),
                "Price": service.get("price"),
                "Duration": service.get("duration"),
                "Active": "Yes" if service.get("is_active") else "No",
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
                st.metric("Price", service.get("price"))

            with col2:
                st.metric("Duration", service.get("duration"))

            with col3:
                if service.get("is_active"):
                    st.success("Active")
                else:
                    st.warning("Inactive")

            st.write(service.get("description") or "No description provided.")

            edit_service_form(service, provider_id)

            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if service.get("is_active"):
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
                            st.error("Could not deactivate service.")
                            st.exception(error)
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
                            st.error("Could not activate service.")
                            st.exception(error)

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
                        st.error("Could not delete service.")
                        st.exception(error)


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
                    value=bool(service.get("is_active")),
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
                st.error("Could not update service.")
                st.exception(error)


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